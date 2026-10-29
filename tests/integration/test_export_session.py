"""GUI snapshot availability and background export coordination."""

from pathlib import Path
from threading import Event, get_ident
import time

import numpy as np
import pytest
import cv2
from PIL import Image

from hsv_segmentation.application.playback import PlaybackState
from hsv_segmentation.application.processing_worker import ProcessingWorker
from hsv_segmentation.errors import WriteError
from hsv_segmentation.gui.controller import ApplicationController
from hsv_segmentation.io.export import ExportReceipt, export_snapshot
from hsv_segmentation.models import HSVThresholdSet


def _create_tk_root(tkinter):
    last_error = None
    for _attempt in range(3):
        try:
            return tkinter.Tk()
        except tkinter.TclError as error:
            last_error = error
            time.sleep(0.05)
    pytest.fail(f"Tk root could not be created after three attempts: {last_error}")


def _wait_for(root, predicate, timeout=4.0):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        root.update()
        time.sleep(0.005)
    assert predicate()


def _open_fixture(controller, root, path: Path, value: int = 80):
    rgb = np.full((3, 4, 3), [value, 20, 10], dtype=np.uint8)
    Image.fromarray(rgb).save(path)
    controller.open_image_path(str(path))
    _wait_for(root, lambda: controller.session.result is not None)
    return controller.session.result


def _write_video(path: Path, frame_count: int = 12) -> None:
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*"MJPG"), 12.0, (12, 8)
    )
    if not writer.isOpened():
        pytest.skip("MJPG AVI writer is unavailable")
    try:
        for index in range(frame_count):
            rgb = np.full(
                (8, 12, 3),
                [(index * 19) % 256, (index * 37) % 256, (index * 53) % 256],
                dtype=np.uint8,
            )
            writer.write(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    finally:
        writer.release()


def test_pending_export_cannot_be_replaced_by_newer_processing_work() -> None:
    active_started = Event()
    release_active = Event()
    worker = ProcessingWorker()

    def active_operation():
        active_started.set()
        assert release_active.wait(3)
        return "active"

    try:
        worker.submit_operation("active", 1, active_operation)
        assert active_started.wait(2)
        worker.submit_operation(
            "export_result", 1, lambda: "export", replace_pending=False
        )
        worker.submit_operation("processing", 2, lambda: "obsolete")
        worker.submit_operation("processing", 3, lambda: "latest")
        release_active.set()

        completions = []
        deadline = time.monotonic() + 3
        while len(completions) < 3 and time.monotonic() < deadline:
            completions.extend(worker.poll())
            time.sleep(0.005)

        assert [(item.kind, item.result) for item in completions] == [
            ("active", "active"),
            ("export_result", "export"),
            ("processing", "latest"),
        ]
    finally:
        release_active.set()
        worker.shutdown()


def test_export_is_unavailable_without_a_complete_current_result(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    controller = ApplicationController(root)
    try:
        assert str(controller.window.save_mask_button.cget("state")) == "disabled"
        assert str(controller.window.save_result_button.cget("state")) == "disabled"
        assert str(controller.window.save_overlay_button.cget("state")) == "disabled"
        assert controller.save_mask_path(None) is False

        _open_fixture(controller, root, (tmp_path / "source.png").resolve())
        assert str(controller.window.save_mask_button.cget("state")) == "normal"
        assert str(controller.window.save_result_button.cget("state")) == "normal"
        assert str(controller.window.save_overlay_button.cget("state")) == "normal"

        controller._on_thresholds(
            HSVThresholdSet(lower_h_deg=20, parameter_revision=1)
        )
        assert controller.save_mask_path((tmp_path / "pending.png").resolve()) is False
    finally:
        controller.close()


def test_cancel_and_declined_overwrite_preserve_destination_and_session(
    tmp_path, monkeypatch
) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    controller = ApplicationController(root)
    try:
        result = _open_fixture(controller, root, (tmp_path / "source.png").resolve())
        destination = (tmp_path / "mask.png").resolve()
        destination.write_bytes(b"keep me")
        assert controller.save_mask_path(None) is False
        monkeypatch.setattr(
            "hsv_segmentation.gui.controller.messagebox.askyesno", lambda *a, **k: False
        )

        assert controller.save_mask_path(destination) is False
        assert destination.read_bytes() == b"keep me"
        assert controller.session.result is result
    finally:
        controller.close()


def test_image_mask_and_result_export_complete_in_background(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    controller = ApplicationController(root)
    try:
        result = _open_fixture(controller, root, (tmp_path / "source.png").resolve())
        mask_path = (tmp_path / "mask.png").resolve()
        result_path = (tmp_path / "result.png").resolve()

        assert controller.save_mask_path(mask_path) is True
        _wait_for(root, lambda: controller.export_in_flight is False)
        assert controller.save_result_path(result_path) is True
        _wait_for(root, lambda: controller.export_in_flight is False)

        np.testing.assert_array_equal(np.asarray(Image.open(mask_path)), result.mask)
        np.testing.assert_array_equal(
            np.asarray(Image.open(result_path).convert("RGB")), result.segmented_rgb
        )
        assert controller.session.result is result
    finally:
        controller.close()


def test_current_overlay_export_matches_preview_snapshot(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    controller = ApplicationController(root)
    try:
        _open_fixture(controller, root, (tmp_path / "source.png").resolve())
        captured = controller.window.overlay_snapshot
        destination = (tmp_path / "overlay.png").resolve()
        assert controller.save_overlay_path(destination)
        _wait_for(root, lambda: not controller.export_in_flight)
        np.testing.assert_array_equal(
            np.asarray(Image.open(destination).convert("RGB")), captured.rgb
        )
        assert controller.last_export_receipt.variant == captured.variant
    finally:
        controller.close()


def test_playing_video_export_uses_one_identified_frame_and_resumes(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    video_path = (tmp_path / "source.avi").resolve()
    output_path = (tmp_path / "video-frame.png").resolve()
    _write_video(video_path)
    controller = ApplicationController(root)
    try:
        controller.open_video_path(str(video_path))
        _wait_for(root, lambda: controller.playback.state is PlaybackState.PAUSED)
        controller.play_video()
        _wait_for(
            root,
            lambda: controller.playback.state is PlaybackState.PLAYING
            and controller.session.result.frame_index >= 1,
        )
        captured = controller.session.result

        assert controller.save_result_path(output_path) is True
        _wait_for(root, lambda: controller.export_in_flight is False)

        receipt = controller.last_export_receipt
        assert receipt.session_id == captured.session_id
        assert receipt.frame_index == captured.frame_index
        np.testing.assert_array_equal(
            np.asarray(Image.open(output_path).convert("RGB")), captured.segmented_rgb
        )
        assert controller.playback.state in {PlaybackState.PLAYING, PlaybackState.ENDED}
    finally:
        controller.close()


def test_delayed_export_keeps_ui_responsive_and_uses_captured_snapshot(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    started = Event()
    release = Event()
    calls = []
    main_thread = get_ident()

    def delayed_export(snapshot, kind, path, *, overwrite=False):
        calls.append((snapshot, kind, Path(path), get_ident()))
        started.set()
        assert release.wait(3)
        return export_snapshot(snapshot, kind, path, overwrite=overwrite)

    controller = ApplicationController(root, exporter=delayed_export)
    try:
        captured = _open_fixture(
            controller, root, (tmp_path / "captured.png").resolve(), value=60
        )
        destination = (tmp_path / "captured-result.png").resolve()
        assert controller.save_result_path(destination) is True
        assert started.wait(2)
        assert calls[0][3] != main_thread
        assert str(controller.window.save_mask_button.cget("state")) == "disabled"
        assert controller.save_mask_path((tmp_path / "duplicate.png").resolve()) is False

        serviced = []
        root.after(0, lambda: serviced.append(True))
        _wait_for(root, lambda: bool(serviced))

        replacement_path = (tmp_path / "replacement.png").resolve()
        Image.fromarray(np.full((3, 4, 3), [180, 20, 10], dtype=np.uint8)).save(
            replacement_path
        )
        controller.open_image_path(str(replacement_path))
        release.set()
        _wait_for(root, lambda: controller.export_in_flight is False)
        _wait_for(
            root,
            lambda: controller.session.result is not None
            and controller.session.result.session_id != captured.session_id,
        )
        replacement = controller.session.result

        assert calls[0][0] is captured
        np.testing.assert_array_equal(
            np.asarray(Image.open(destination).convert("RGB")), captured.segmented_rgb
        )
        assert controller.last_export_receipt.source_path.name == "captured.png"
        assert controller.session.result is replacement
    finally:
        release.set()
        controller.close()


def test_close_during_delayed_export_discards_late_ui_completion(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    started = Event()
    release = Event()

    def delayed_export(snapshot, kind, path, *, overwrite=False):
        started.set()
        assert release.wait(3)
        return ExportReceipt(
            kind=kind,
            path=Path(path).resolve(),
            source_path=snapshot.source.source_path,
            session_id=snapshot.session_id,
            frame_index=snapshot.frame_index,
        )

    controller = ApplicationController(root, exporter=delayed_export)
    _open_fixture(controller, root, (tmp_path / "source.png").resolve())
    assert controller.save_mask_path((tmp_path / "late.png").resolve()) is True
    assert started.wait(2)
    controller.close()
    release.set()
    time.sleep(0.05)
    assert controller._closed is True


def test_background_write_failure_preserves_result_and_allows_retry(
    tmp_path, monkeypatch
) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    errors = []

    def failing_export(snapshot, kind, path, *, overwrite=False):
        raise WriteError(
            "simulated destination failure; choose another directory and retry",
            path=path,
            operation="save result PNG",
        )

    monkeypatch.setattr(
        "hsv_segmentation.gui.controller.messagebox.showerror",
        lambda title, message, **kwargs: errors.append((title, message)),
    )
    controller = ApplicationController(root, exporter=failing_export)
    try:
        result = _open_fixture(controller, root, (tmp_path / "source.png").resolve())
        assert controller.save_result_path((tmp_path / "failed.png").resolve()) is True
        _wait_for(root, lambda: controller.export_in_flight is False)

        assert errors and "simulated destination failure" in errors[0][1]
        assert all(
            label in errors[0][1]
            for label in ("Operation:", "Affected:", "Cause:", "Preserved:", "Action:")
        )
        assert controller.session.result is result
        assert str(controller.window.save_result_button.cget("state")) == "normal"
    finally:
        controller.close()
