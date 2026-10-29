"""Acceptance checks for the clean desktop analysis workspace."""

import time

import pytest

from hsv_segmentation.gui.main_window import MainWindow
from hsv_segmentation.gui.controller import ApplicationController
from hsv_segmentation.gui.theme import COLORS, configure_theme
from hsv_segmentation.gui.threshold_controls import ThresholdControls


def _root(tkinter):
    last_error = None
    for _attempt in range(3):
        try:
            return tkinter.Tk()
        except tkinter.TclError as error:
            last_error = error
            time.sleep(0.05)
    pytest.fail(f"Tk root could not be created: {last_error}")


def test_theme_exposes_semantic_roles_and_primary_style() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _root(tkinter)
    try:
        style = configure_theme(root)
        assert {
            "background", "surface", "text", "muted_text", "border",
            "primary", "on_primary", "focus", "disabled", "error",
            "success", "warning", "surface_raised",
        } <= COLORS.keys()
        assert COLORS["background"] == "#090f1c"
        assert style.lookup("TFrame", "background") == COLORS["surface"]
        assert style.lookup("Primary.TButton", "background") == COLORS["primary"]
        assert style.lookup("Status.TLabel", "foreground") == COLORS["muted_text"]
        assert style.lookup("Metric.TLabel", "foreground") == COLORS["primary"]
    finally:
        root.destroy()


def test_threshold_controls_group_lower_and_upper_values_by_channel() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _root(tkinter)
    root.withdraw()
    try:
        controls = ThresholdControls(root)
        assert controls.layout_orientation == "horizontal"
        assert tuple(controls.channel_groups) == ("h", "s", "v")
        assert set(controls.fields) == {
            "lower_h_deg", "upper_h_deg", "lower_s_pct",
            "upper_s_pct", "lower_v_pct", "upper_v_pct",
        }
    finally:
        root.destroy()


def test_workspace_context_hides_video_controls_until_video_is_active() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _root(tkinter)
    try:
        window = MainWindow(root)
        root.update()
        assert window.media_context == "empty"
        assert window.video_controls.winfo_manager() == ""

        window.update_video_controls("paused")
        root.update()
        assert window.media_context == "video"
        assert window.video_controls.winfo_manager() == "pack"
        assert str(window.play_button.cget("state")) == "normal"
        assert window.input_section.winfo_reqwidth() <= window.input_section.winfo_width()

        window.set_media_context("image")
        root.update_idletasks()
        assert window.video_controls.winfo_manager() == ""
        assert window.frame_var.get() == "Frame: —"
    finally:
        root.destroy()


def test_workspace_shortcuts_and_minimum_preview_area() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _root(tkinter)
    controller = ApplicationController(root)
    try:
        window = controller.window
        root.geometry("1100x720")
        window.update_video_controls("paused")
        root.update()

        assert root.bind("<Control-o>")
        assert root.bind("<Control-Shift-O>")
        assert tuple(window.control_sections) == ("hsv", "refine", "analyze")
        assert len(window.control_notebook.tabs()) == 3
        assert window.parameter_section.winfo_width() == window.workspace.winfo_width()
        assert all(view.canvas.winfo_width() >= 160 for view in window.views)
        assert all(view.canvas.winfo_height() >= 120 for view in window.views)
        assert controller.controls.winfo_height() >= controller.controls.winfo_reqheight()

        window.control_notebook.select(window.refine_controls_tab)
        root.update()
        assert (
            controller.morphology_controls.winfo_height()
            >= controller.morphology_controls.winfo_reqheight()
        )
        assert (
            controller.watershed_controls.winfo_height()
            >= controller.watershed_controls.winfo_reqheight()
        )
        assert controller.watershed_controls.master is window.refine_controls_tab

        window.control_notebook.select(window.analysis_controls_tab)
        root.update()
        assert not hasattr(controller.analysis_panel, "detail_notebook")
        assert (
            controller.analysis_panel.winfo_height()
            >= controller.analysis_panel.winfo_reqheight()
        )
        assert window.histogram_visible is True
    finally:
        controller.close()
