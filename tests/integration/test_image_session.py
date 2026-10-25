"""Still-image session, worker coalescing, and GUI structure regressions."""

from pathlib import Path
from threading import Event
import time

import numpy as np
import pytest
from PIL import Image

from hsv_segmentation.application.processing_worker import ProcessingWorker
from hsv_segmentation.application.session import ImageSession, process_source
from hsv_segmentation.gui.controller import ApplicationController
from hsv_segmentation.gui.image_view import ImageView
from hsv_segmentation.gui.main_window import MainWindow
from hsv_segmentation.gui.threshold_controls import ThresholdControls
from hsv_segmentation.models import HSVThresholdSet, InputMedia, ProcessingRequest
from hsv_segmentation.processing.segmentation import segment


def _media(tmp_path: Path) -> InputMedia:
    return InputMedia(
        source_path=(tmp_path / "memory.png").resolve(),
        source_sha256="a" * 64,
        source_format="PNG",
        rgb=np.array([[[255, 0, 0], [0, 255, 0]]], dtype=np.uint8),
    )


def _create_tk_root(tkinter):
    last_error = None
    for _attempt in range(3):
        try:
            return tkinter.Tk()
        except tkinter.TclError as error:
            last_error = error
            time.sleep(0.05)
    pytest.fail(f"Tk root could not be created after three attempts: {last_error}")


def test_worker_keeps_one_active_and_only_latest_pending_request(tmp_path) -> None:
    source = _media(tmp_path)
    first_started = Event()
    release_first = Event()

    def slow_processor(request: ProcessingRequest):
        if request.request_revision == 1:
            first_started.set()
            assert release_first.wait(2)
        return process_source(request.source, request.thresholds, request.request_revision)

    worker = ProcessingWorker(processor=slow_processor)
    requests = [
        ProcessingRequest(
            source,
            HSVThresholdSet(lower_h_deg=value, parameter_revision=value),
            request_revision=value,
        )
        for value in (1, 2, 3)
    ]
    try:
        worker.submit(requests[0])
        assert first_started.wait(2)
        worker.submit(requests[1])
        worker.submit(requests[2])
        release_first.set()

        deadline = time.monotonic() + 3
        completions = []
        while len(completions) < 2 and time.monotonic() < deadline:
            completions.extend(worker.poll())
            time.sleep(0.01)

        assert [item.request_revision for item in completions] == [1, 3]
        assert completions[-1].result is not None
        assert completions[-1].result.parameter_revision == 3
    finally:
        worker.shutdown()


def test_worker_cleans_late_resource_when_shutdown_during_operation() -> None:
    started = Event()
    release_operation = Event()
    cleaned = Event()
    resource = object()

    def operation():
        started.set()
        assert release_operation.wait(2)
        return resource

    worker = ProcessingWorker()
    worker.submit_operation(
        "resource", 1, operation,
        cleanup=lambda completed: cleaned.set() if completed is resource else None,
    )
    assert started.wait(2)
    worker.shutdown()
    release_operation.set()
    assert cleaned.wait(2)


def test_session_discards_stale_threshold_result(tmp_path) -> None:
    source = _media(tmp_path)
    session = ImageSession()
    initial = process_source(source, HSVThresholdSet(), 1)
    session.commit_candidate(initial)
    latest_thresholds = HSVThresholdSet(lower_h_deg=120, parameter_revision=2)
    session.accept_thresholds(latest_thresholds)

    stale = process_source(
        source, HSVThresholdSet(lower_h_deg=60, parameter_revision=1), 2
    )
    current = process_source(source, latest_thresholds, 3)

    assert session.commit_result(stale) is False
    assert session.commit_result(current) is True
    assert session.result is current
    assert session.thresholds is latest_thresholds


def test_processing_never_changes_source_file(tmp_path) -> None:
    path = (tmp_path / "source.png").resolve()
    Image.fromarray(np.array([[[255, 0, 0], [0, 255, 0]]], dtype=np.uint8)).save(path)
    original_bytes = path.read_bytes()
    session = ImageSession()

    session.open_image(path)
    session.set_thresholds(HSVThresholdSet(lower_h_deg=350, upper_h_deg=10))

    assert path.read_bytes() == original_bytes


def test_window_has_named_sections_three_views_and_six_controls() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    try:
        window = MainWindow(root)
        controls = ThresholdControls(window.parameter_section)
        root.update_idletasks()

        assert root.title() == "HSV Color Segmentation"
        assert window.input_section.cget("text") == "File Input"
        assert window.parameter_section.cget("text") == "HSV Parameters"
        assert window.visualization_section.cget("text") == "Result Visualization"
        assert [view.cget("text") for view in window.views] == [
            "Original", "Binary Mask", "Segmented Result"
        ]
        assert len(controls.fields) == 6
        assert "360" in controls.range_text
        assert "wrap" in controls.range_text.lower()
    finally:
        root.destroy()


def test_image_view_supports_zoom_fit_and_scrollable_canvas() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.geometry("480x320")
    try:
        view = ImageView(root, title="Zoom test")
        view.pack(fill="both", expand=True)
        image = np.zeros((600, 900, 3), dtype=np.uint8)
        image[100:500, 200:700] = [40, 120, 220]
        view.show_array(image)
        root.update()

        assert view.zoom_factor == 1.0
        assert view.canvas.cget("scrollregion")
        assert view.zoom_text == "Fit"

        view.zoom_in()
        root.update()
        assert view.zoom_factor > 1.0
        assert "%" in view.zoom_text

        view.zoom_out()
        view.fit()
        root.update()
        assert view.zoom_factor == 1.0
        assert view.zoom_text == "Fit"
        np.testing.assert_array_equal(view.source_array, image)
    finally:
        root.destroy()


def test_threshold_controls_report_invalid_edit_without_callback() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    accepted = []
    try:
        controls = ThresholdControls(root, on_valid=accepted.append, debounce_ms=0)
        controls.fields["lower_s_pct"].set("90")
        controls.fields["upper_s_pct"].set("20")
        controls.validate_now()

        assert accepted == []
        assert "lower_s_pct" in controls.error_text

        controls.fields["upper_s_pct"].set("100")
        controls.validate_now()
        assert accepted[-1].lower_s_pct == 90
        assert accepted[-1].upper_s_pct == 100
    finally:
        root.destroy()


def test_controller_open_and_rapid_edits_present_only_final_snapshot(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    path = (tmp_path / "colors.png").resolve()
    rgb = np.array(
        [[[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 255]]],
        dtype=np.uint8,
    )
    Image.fromarray(rgb).save(path)
    controller = ApplicationController(root)
    try:
        controller.open_image_path(str(path))
        deadline = time.monotonic() + 3
        while controller.session.result is None and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert controller.session.result is not None

        final_thresholds = None
        for revision, lower_hue in enumerate((30, 60, 120), start=1):
            final_thresholds = HSVThresholdSet(
                lower_h_deg=lower_hue,
                upper_h_deg=240,
                parameter_revision=revision,
            )
            controller._on_thresholds(final_thresholds)

        deadline = time.monotonic() + 3
        while (
            controller.session.result is None
            or controller.session.result.parameter_revision != final_thresholds.parameter_revision
        ) and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)

        result = controller.session.result
        assert result is not None
        assert result.thresholds == final_thresholds
        expected_mask, expected_rgb = segment(rgb, final_thresholds)
        np.testing.assert_array_equal(result.mask, expected_mask)
        np.testing.assert_array_equal(result.segmented_rgb, expected_rgb)
        np.testing.assert_array_equal(controller.window.mask_view.source_array, expected_mask)
        np.testing.assert_array_equal(
            controller.window.result_view.source_array, expected_rgb
        )
    finally:
        controller.close()
