"""Experiment publication and GUI background-coordination checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from threading import Event, get_ident
import time
from uuid import UUID

import numpy as np
import pytest
from PIL import Image

from hsv_segmentation.application.session import process_source
from hsv_segmentation.errors import WriteError
from hsv_segmentation.gui.controller import ApplicationController
from hsv_segmentation.io.experiments import (
    ExperimentReceipt,
    pixel_sha256,
    publish_experiment,
)
from hsv_segmentation.io.images import load_image
from hsv_segmentation.models import HSVThresholdSet


def _snapshot(tmp_path: Path):
    path = (tmp_path / "source.png").resolve()
    rgb = np.array(
        [[[255, 0, 0], [0, 255, 0]], [[0, 0, 255], [255, 255, 255]]],
        dtype=np.uint8,
    )
    Image.fromarray(rgb).save(path)
    return process_source(
        load_image(path),
        HSVThresholdSet(lower_h_deg=350, upper_h_deg=10, parameter_revision=2),
        3,
    )


def _environment(tmp_path: Path) -> Path:
    path = (tmp_path / "environment.json").resolve()
    path.write_text('{"python":"test"}\n', encoding="utf-8")
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _wait_for(root, predicate, timeout=4.0):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        root.update()
        time.sleep(0.005)
    assert predicate()


def test_publication_writes_complete_versioned_record_and_exact_artifacts(tmp_path) -> None:
    snapshot = _snapshot(tmp_path)
    environment = _environment(tmp_path)

    receipt = publish_experiment(
        snapshot,
        lighting="Controlled indoor test light",
        observations="Red pixels retained; other hues rejected.",
        runs_dir=tmp_path / "runs",
        environment_path=environment,
    )
    record = json.loads(receipt.record_path.read_text(encoding="utf-8"))

    assert record["schema_version"] == 1
    assert UUID(record["run_id"]) == receipt.run_id
    assert record["created_at"].endswith("Z")
    assert record["thresholds"] == snapshot.thresholds.as_dict()
    assert record["morphology"] == snapshot.morphology.as_dict()
    assert record["source"]["width"] == snapshot.width
    assert record["source"]["height"] == snapshot.height
    assert record["source"]["frame_index"] is None
    assert record["source"]["sha256"] == snapshot.source.source_sha256
    assert record["lighting"] == "Controlled indoor test light"
    assert record["observations"]

    mask_path = receipt.run_dir / record["artifacts"]["mask"]["path"]
    result_path = receipt.run_dir / record["artifacts"]["result"]["path"]
    environment_resolved = (receipt.run_dir / record["environment"]["path"]).resolve()
    np.testing.assert_array_equal(np.asarray(Image.open(mask_path)), snapshot.mask)
    np.testing.assert_array_equal(
        np.asarray(Image.open(result_path).convert("RGB")), snapshot.segmented_rgb
    )
    assert environment_resolved == environment
    assert record["environment"]["sha256"] == _sha(environment)
    for artifact, array in (("mask", snapshot.mask), ("result", snapshot.segmented_rgb)):
        item = record["artifacts"][artifact]
        assert len(item["sha256"]) == 64 and item["sha256"].islower()
        assert item["sha256"] == _sha(receipt.run_dir / item["path"])
        assert item["pixel_sha256"] == pixel_sha256(array)


def test_each_publication_uses_a_unique_uuid_directory(tmp_path) -> None:
    snapshot = _snapshot(tmp_path)
    environment = _environment(tmp_path)
    kwargs = dict(
        lighting="Lab light",
        observations="Repeatability run",
        runs_dir=tmp_path / "runs",
        environment_path=environment,
    )
    first = publish_experiment(snapshot, **kwargs)
    second = publish_experiment(snapshot, **kwargs)

    assert first.run_id != second.run_id
    assert first.run_dir != second.run_dir
    assert first.record_path.exists() and second.record_path.exists()


@pytest.mark.parametrize("field", ["lighting", "observations"])
def test_publication_rejects_blank_descriptions_before_creating_run(tmp_path, field) -> None:
    kwargs = dict(
        lighting="Indoor light",
        observations="Useful observation",
        runs_dir=tmp_path / "runs",
        environment_path=_environment(tmp_path),
    )
    kwargs[field] = "  "
    with pytest.raises(ValueError, match=field):
        publish_experiment(_snapshot(tmp_path), **kwargs)
    assert not (tmp_path / "runs").exists()


def test_failed_artifact_never_publishes_complete_record(tmp_path, monkeypatch) -> None:
    from hsv_segmentation.io import experiments

    def fail_result(*args, **kwargs):
        raise WriteError("simulated artifact failure", operation="record experiment")

    monkeypatch.setattr(experiments, "save_result_png", fail_result)
    with pytest.raises(WriteError, match="simulated artifact failure"):
        publish_experiment(
            _snapshot(tmp_path),
            lighting="Indoor light",
            observations="Failure path",
            runs_dir=tmp_path / "runs",
            environment_path=_environment(tmp_path),
        )
    assert list((tmp_path / "runs").rglob("record.json")) == []


def test_record_action_runs_off_gui_thread_disables_duplicates_and_keeps_identity(
    tmp_path,
) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = tkinter.Tk()
    root.withdraw()
    started = Event()
    release = Event()
    calls = []
    main_thread = get_ident()

    def delayed_recorder(snapshot, lighting, observations, runs_dir, environment_path):
        calls.append((snapshot, lighting, observations, get_ident()))
        started.set()
        assert release.wait(3)
        return publish_experiment(
            snapshot, lighting, observations, runs_dir, environment_path
        )

    controller = ApplicationController(root, experiment_recorder=delayed_recorder)
    try:
        source = _snapshot(tmp_path).source.source_path
        controller.open_image_path(str(source))
        _wait_for(root, lambda: controller.session.result is not None)
        captured = controller.session.result
        controller.experiment_panel.lighting_var.set("Window daylight")
        controller.experiment_panel.set_observations("Captured before source replacement")

        assert controller.record_experiment_to(
            tmp_path / "runs", _environment(tmp_path)
        ) is True
        assert started.wait(2)
        assert calls[0][3] != main_thread
        assert controller.record_experiment_to(
            tmp_path / "other-runs", _environment(tmp_path)
        ) is False
        assert str(controller.window.record_experiment_button.cget("state")) == "disabled"

        serviced = []
        root.after(0, lambda: serviced.append(True))
        _wait_for(root, lambda: serviced)
        replacement = (tmp_path / "replacement.png").resolve()
        Image.fromarray(np.full((2, 2, 3), 120, dtype=np.uint8)).save(replacement)
        controller.open_image_path(str(replacement))
        release.set()
        _wait_for(root, lambda: controller.export_in_flight is False)
        _wait_for(root, lambda: controller.session.result.session_id != captured.session_id)

        assert calls[0][0] is captured
        assert isinstance(controller.last_experiment_receipt, ExperimentReceipt)
        record = json.loads(
            controller.last_experiment_receipt.record_path.read_text(encoding="utf-8")
        )
        assert record["source"]["sha256"] == captured.source.source_sha256
    finally:
        release.set()
        controller.close()


def test_close_during_delayed_publication_discards_late_ui_completion(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = tkinter.Tk()
    root.withdraw()
    started = Event()
    release = Event()

    def delayed_recorder(snapshot, lighting, observations, runs_dir, environment_path):
        started.set()
        assert release.wait(3)
        run_dir = Path(runs_dir) / "placeholder"
        return ExperimentReceipt(UUID(int=0), run_dir, run_dir / "record.json")

    controller = ApplicationController(root, experiment_recorder=delayed_recorder)
    source = _snapshot(tmp_path).source.source_path
    controller.open_image_path(str(source))
    _wait_for(root, lambda: controller.session.result is not None)
    controller.experiment_panel.lighting_var.set("Indoor")
    controller.experiment_panel.set_observations("Close safety")
    assert controller.record_experiment_to(tmp_path / "runs", _environment(tmp_path))
    assert started.wait(2)
    controller.close()
    release.set()
    time.sleep(0.05)
    assert controller._closed is True


def test_failed_record_preserves_result_and_can_be_retried(tmp_path, monkeypatch) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = tkinter.Tk()
    root.withdraw()
    errors = []
    attempts = 0

    def recorder(snapshot, lighting, observations, runs_dir, environment_path):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise WriteError(
                "simulated record failure; choose another directory and retry",
                path=runs_dir,
                operation="record experiment",
            )
        return publish_experiment(
            snapshot, lighting, observations, runs_dir, environment_path
        )

    monkeypatch.setattr(
        "hsv_segmentation.gui.controller.messagebox.showerror",
        lambda title, message, **kwargs: errors.append(message),
    )
    controller = ApplicationController(root, experiment_recorder=recorder)
    try:
        source = _snapshot(tmp_path).source.source_path
        controller.open_image_path(str(source))
        _wait_for(root, lambda: controller.session.result is not None)
        retained = controller.session.result
        controller.experiment_panel.lighting_var.set("Indoor")
        controller.experiment_panel.set_observations("Retry behavior")
        environment = _environment(tmp_path)

        assert controller.record_experiment_to(tmp_path / "failed-runs", environment)
        _wait_for(root, lambda: controller.export_in_flight is False)
        assert controller.session.result is retained
        assert errors and "Action:" in errors[-1]
        assert str(controller.window.record_experiment_button.cget("state")) == "normal"

        assert controller.record_experiment_to(tmp_path / "successful-runs", environment)
        _wait_for(root, lambda: controller.export_in_flight is False)
        assert controller.last_experiment_receipt.record_path.is_file()
        assert controller.session.result is retained
    finally:
        controller.close()
