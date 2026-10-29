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
from hsv_segmentation.processing.visualization import compose_segmentation_overlay


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
        assert worker.is_busy is False
        worker.submit(requests[0])
        assert first_started.wait(2)
        assert worker.is_busy is True
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
        assert worker.is_busy is False
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


def test_window_has_named_sections_four_views_and_six_controls() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    try:
        window = MainWindow(root)
        controls = ThresholdControls(window.hsv_controls_tab)
        root.update_idletasks()

        assert root.title() == "HSV Color Segmentation"
        assert window.input_section.winfo_class() == "TFrame"
        assert window.parameter_section.winfo_class() == "TFrame"
        assert window.visualization_section.winfo_class() == "TFrame"
        assert [view.cget("text") for view in window.views] == [
            "Original", "Binary Mask", "Segmented Result", "Overlay"
        ]
        assert len(controls.fields) == 6
        assert controls.range_text == (
            "Hue range: 0–360° | Saturation: 0–100% | Value: 0–100%"
        )
        assert controls.selected_text == (
            "Selected HSV: H [0°, 360°], S [0%, 100%], V [0%, 100%]"
        )
    finally:
        root.destroy()


def test_compact_controls_preserve_four_usable_views_at_minimum_size() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    controller = ApplicationController(root)
    try:
        root.geometry("1100x720")
        root.update()

        assert len(controller.window.views) == 4
        assert all(view.canvas.winfo_width() >= 160 for view in controller.window.views)
        assert all(view.canvas.winfo_height() >= 120 for view in controller.window.views)
    finally:
        controller.close()


def test_image_view_supports_zoom_fit_and_scrollable_canvas() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.geometry("480x320")
    try:
        view = ImageView(root, title="Zoom test")
        view.pack(fill="both", expand=True)
        root.update()

        assert view.placeholder_text == "Open an image or video to begin"
        assert view.canvas.cget("background") != ImageView.IMAGE_BACKGROUND
        assert view.canvas.itemcget(view._placeholder_item, "text") == view.placeholder_text

        image = np.zeros((600, 900, 3), dtype=np.uint8)
        image[100:500, 200:700] = [40, 120, 220]
        view.show_array(image)
        root.update()

        assert view.canvas.cget("background") == ImageView.IMAGE_BACKGROUND
        left, top, width, height = view._display_bounds
        assert view.source_pixel_at_canvas(left, top) == (0, 0)
        assert view.source_pixel_at_canvas(
            left + width - 0.01, top + height - 0.01
        ) == (899, 599)
        assert view.source_pixel_at_canvas(left - 1, top) is None
        assert view.source_roi_at_canvas(
            left, top, left + width, top + height
        ) == (0, 0, 900, 600)
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
        assert controls.selected_text == (
            "Selected HSV: H [0°, 360°], S [0%, 100%], V [0%, 100%]"
        )

        controls.fields["upper_s_pct"].set("100")
        controls.validate_now()
        assert accepted[-1].lower_s_pct == 90
        assert accepted[-1].upper_s_pct == 100
        assert controls.selected_text == (
            "Selected HSV: H [0°, 360°], S [90%, 100%], V [0%, 100%]"
        )
    finally:
        root.destroy()


def test_threshold_sliders_numeric_inputs_presets_and_reset_stay_synchronized() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    accepted = []
    try:
        controls = ThresholdControls(root, on_valid=accepted.append, debounce_ms=0)

        controls._on_slider("lower_h_deg", "29")
        controls.validate_now()
        assert controls.fields["lower_h_deg"].get() == "29"
        assert accepted[-1].lower_h_deg == 29

        controls.fields["upper_h_deg"].set("48")
        controls.validate_now()
        assert round(controls.sliders["upper_h_deg"].get()) == 48
        assert accepted[-1].upper_h_deg == 48

        controls.apply_preset("Red")
        assert controls.preset_name == "Red"
        assert accepted[-1].wraps_hue
        assert controls.fields["lower_s_pct"].get() == "50"

        controls.reset()
        assert controls.preset_name == "Custom"
        assert accepted[-1].as_dict() == HSVThresholdSet().as_dict()
        assert all(
            round(controls.sliders[name].get()) == getattr(accepted[-1], name)
            for name in controls.sliders
        )
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
        np.testing.assert_array_equal(
            controller.window.result_view.source_array, expected_rgb
        )
        np.testing.assert_array_equal(
            controller.window.overlay_view.source_array,
            compose_segmentation_overlay(rgb, expected_mask),
        )
        assert controller.window.overlay_view.cget("text") == "Overlay"
        assert controller.session.result.segmented_rgb is result.segmented_rgb
    finally:
        controller.close()


def test_controller_color_picker_applies_suggestion_and_updates_selection(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    path = (tmp_path / "picker.png").resolve()
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

        assert not controller.experiment_panel.visible
        root.deiconify()
        controller.window.record_experiment_button.invoke()
        root.update()
        assert controller.experiment_panel.visible
        controller.experiment_panel.hide()

        controller.toggle_color_picker()
        assert controller.window.original_view.sampling_enabled
        controller._on_color_sample(0, 0)
        assert not controller.window.original_view.sampling_enabled
        assert controller.session.thresholds.wraps_hue
        assert "H 0.0°" in controller.window.sample_var.get()

        expected_revision = controller.session.thresholds.parameter_revision
        deadline = time.monotonic() + 3
        while (
            controller.session.result is None
            or controller.session.result.parameter_revision != expected_revision
        ) and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)

        assert controller.session.result.selected_pixel_count == 1
        assert "25.00%" in controller.window.selection_var.get()
    finally:
        controller.close()


def test_controller_roi_picker_applies_region_thresholds(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    path = (tmp_path / "roi-picker.png").resolve()
    rgb = np.array(
        [[[255, 0, 30], [255, 20, 0], [0, 255, 0], [0, 0, 255]]],
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

        controller.window.sampling_mode_var.set("ROI")
        controller.window._apply_sampling_mode()
        controller.toggle_color_picker()
        assert controller.window.original_view.sampling_mode == "roi"
        controller._on_roi_sample(0, 0, 2, 1)

        assert controller.session.thresholds.wraps_hue
        assert "ROI 2×1" in controller.window.sample_var.get()
        assert "2 pixels" in controller.window.status_var.get()
    finally:
        controller.close()


def test_controller_multi_picker_combines_up_to_four_points_and_preserves_pixel_mode(
    tmp_path,
) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    path = (tmp_path / "multi-picker.png").resolve()
    rgb = np.array(
        [[[255, 0, 43], [255, 0, 0], [255, 43, 0], [128, 0, 0]]],
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

        controller.window.sampling_mode_var.set("Multi")
        controller.window._apply_sampling_mode()
        controller.toggle_color_picker()
        assert controller.window.original_view.sampling_mode == "multi"

        controller._on_color_sample(0, 0)
        assert controller._color_picker_active
        assert "Multi 1/4" in controller.window.sample_var.get()

        controller._on_color_sample(1, 0)
        controller._on_color_sample(2, 0)
        assert controller._color_picker_active
        assert "Multi 3/4" in controller.window.sample_var.get()
        assert controller.session.thresholds.wraps_hue

        controller._on_color_sample(3, 0)
        assert not controller._color_picker_active
        assert "Multi 4/4" in controller.window.sample_var.get()
        assert "4 selected pixels" in controller.window.status_var.get()

        controller.window.sampling_mode_var.set("Pixel")
        controller.window._apply_sampling_mode()
        controller.toggle_color_picker()
        controller._on_color_sample(1, 0)
        assert not controller._color_picker_active
        assert "H 0.0°" in controller.window.sample_var.get()
    finally:
        controller.close()


def test_morphology_pipeline_comparison_and_exports_use_processed_mask(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    path = (tmp_path / "morphology.png").resolve()
    rgb = np.zeros((7, 7, 3), dtype=np.uint8)
    rgb[2:5, 2:5] = [255, 0, 0]
    rgb[0, 0] = [255, 0, 0]
    Image.fromarray(rgb).save(path)
    controller = ApplicationController(root)
    try:
        controller.controls.apply_thresholds(HSVThresholdSet(
            lower_h_deg=350,
            upper_h_deg=10,
            lower_s_pct=50,
            upper_s_pct=100,
            lower_v_pct=50,
            upper_v_pct=100,
        ))
        controller.morphology_controls.enabled_var.set(True)
        controller.morphology_controls.operation_var.set("Opening")
        controller.morphology_controls.kernel_var.set("3×3")
        controller.morphology_controls._changed()
        controller.open_image_path(str(path))

        deadline = time.monotonic() + 3
        while controller.session.result is None and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        result = controller.session.result
        assert result is not None and result.morphology.enabled
        assert np.count_nonzero(result.original_mask) == 10
        assert np.count_nonzero(result.mask) == 9
        np.testing.assert_array_equal(controller.window.mask_view.source_array, result.mask)
        assert controller.window.mask_view.cget("text") == "Post-processed Mask"

        controller.window.original_mask_var.set(True)
        controller.window._refresh_mask_view()
        np.testing.assert_array_equal(
            controller.window.mask_view.source_array, result.original_mask
        )
        assert controller.window.mask_view.cget("text") == "Original HSV Mask"

        mask_path = tmp_path / "saved-mask.png"
        result_path = tmp_path / "saved-result.png"
        assert controller.save_mask_path(mask_path)
        deadline = time.monotonic() + 3
        while controller.export_in_flight and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert controller.save_result_path(result_path)
        deadline = time.monotonic() + 3
        while controller.export_in_flight and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)

        np.testing.assert_array_equal(np.asarray(Image.open(mask_path)), result.mask)
        np.testing.assert_array_equal(
            np.asarray(Image.open(result_path).convert("RGB")), result.segmented_rgb
        )
    finally:
        controller.close()
