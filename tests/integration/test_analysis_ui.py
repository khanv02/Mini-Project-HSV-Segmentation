import time

import numpy as np
import pytest
from PIL import Image

from hsv_segmentation.gui.controller import ApplicationController
from hsv_segmentation.gui.watershed_controls import WatershedControls
from hsv_segmentation.models import AnalysisSettings


def _root():
    tkinter = pytest.importorskip("tkinter")
    try:
        root = tkinter.Tk(); root.withdraw(); return root
    except tkinter.TclError as error:
        pytest.skip(f"Tk unavailable: {error}")


def _wait(root, predicate, timeout=5):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        root.update(); time.sleep(0.005)
    assert predicate()


def test_analysis_controls_update_statistics_without_changing_baseline(tmp_path) -> None:
    root = _root(); controller = ApplicationController(root)
    try:
        rgb = np.zeros((40, 40, 3), np.uint8)
        rgb[5:12, 5:12] = (255, 0, 0); rgb[20:30, 25:35] = (255, 0, 0)
        path = tmp_path / "objects.png"; Image.fromarray(rgb).save(path)
        controller.open_image_path(str(path))
        _wait(root, lambda: controller.session.result is not None)
        baseline = controller.session.result.mask.copy()
        controller._on_analysis_settings(AnalysisSettings(True, 8, 4), "baseline")
        _wait(root, lambda: controller.session.result.analysis is not None)
        result = controller.session.result
        np.testing.assert_array_equal(result.mask, baseline)
        assert result.analysis.retained_count == 1  # full-domain HSV mask is one full-image region
        assert "Connected regions" in controller.analysis_panel.summary_var.get()
        assert len(controller.analysis_panel.tree.get_children()) == 1
    finally:
        controller.close()


def test_analysis_panel_is_compact_and_discloses_metric_state() -> None:
    root = _root(); controller = ApplicationController(root)
    try:
        root.deiconify(); root.geometry("1100x720")
        controller.window.control_notebook.select(
            controller.window.analysis_controls_tab
        )
        root.update()
        assert controller.analysis_panel.winfo_reqwidth() <= 1000
        assert controller.analysis_panel.winfo_reqheight() <= 150
        assert (
            controller.analysis_panel.winfo_reqheight()
            <= controller.analysis_panel.winfo_height()
        )
        assert "IoU" in controller.analysis_panel.metrics_var.get()
        assert all(view.canvas.winfo_width() >= 160 for view in controller.window.views)
    finally:
        controller.close()


def test_analysis_panel_disables_advanced_fields_until_enabled() -> None:
    root = _root(); controller = ApplicationController(root)
    try:
        panel = controller.analysis_panel
        assert str(panel.connectivity_box.cget("state")) == "disabled"
        assert str(panel.min_area_entry.cget("state")) == "disabled"
        assert str(panel.contours_button.cget("state")) == "disabled"
        assert not hasattr(panel, "seed_entry")
        assert not hasattr(panel, "watershed_var")
        assert str(controller.watershed_controls.seed_entry.cget("state")) == "disabled"
        assert str(controller.watershed_controls.seed_scale.cget("state")) == "disabled"

        panel.enabled_var.set(True)
        panel._emit()
        assert str(panel.connectivity_box.cget("state")) == "readonly"
        assert str(panel.min_area_entry.cget("state")) == "normal"
        assert str(panel.contours_button.cget("state")) == "normal"

        controller.watershed_controls.enabled_var.set(True)
        controller.watershed_controls._changed()
        assert str(controller.watershed_controls.seed_entry.cget("state")) == "normal"
        assert str(controller.watershed_controls.seed_scale.cget("state")) == "normal"
        assert str(panel.contours_button.cget("state")) == "normal"
    finally:
        controller.close()


def test_watershed_seed_slider_emits_only_after_release() -> None:
    root = _root(); emitted = []
    try:
        controls = WatershedControls(root, on_change=emitted.append)
        controls.enable_button.invoke()
        emitted.clear()

        controls.seed_var.set(0.7)
        controls._scale_changed("0.7")
        root.update()
        assert emitted == []
        assert "Release slider" in controls.status_var.get()
        controls._commit_scale()

        assert len(emitted) == 1
        assert emitted[0].enabled is True
        assert emitted[0].seed_fraction == pytest.approx(0.7)
        assert controls.seed_value_var.get() == "0.70"
        controls._changed()
        assert len(emitted) == 1
    finally:
        root.destroy()
