"""Tk behavior for explicit grayscale mode controls."""

import time

import pytest

from hsv_segmentation.gui.grayscale_controls import GrayscaleControls
from hsv_segmentation.gui.hsv_histogram import HSVHistogramPanel


def _root(tkinter):
    last = None
    for _ in range(3):
        try:
            root = tkinter.Tk()
            root.withdraw()
            return root
        except tkinter.TclError as error:
            last = error
            time.sleep(0.05)
    pytest.fail(f"Tk root could not be created: {last}")


def test_grayscale_controls_are_opt_in_and_reject_ineligible_source():
    tkinter = pytest.importorskip("tkinter")
    root = _root(tkinter)
    modes = []
    try:
        controls = GrayscaleControls(root, on_mode=modes.append)
        assert controls.mode == "hsv"
        controls.set_source_eligibility(False, "RGB channels differ")
        controls.mode_var.set("Grayscale")
        controls._mode_changed()
        assert controls.mode == "hsv"
        assert not modes
        assert "preserved" in controls.status_var.get().lower()
    finally:
        root.destroy()


def test_manual_and_otsu_controls_preserve_manual_value():
    tkinter = pytest.importorskip("tkinter")
    root = _root(tkinter)
    settings = []
    try:
        controls = GrayscaleControls(root, on_settings=settings.append)
        controls.set_source_eligibility(True)
        controls.mode_var.set("Grayscale")
        controls._mode_changed()
        controls.threshold_var.set(42)
        controls._settings_changed()
        controls.source_var.set("Otsu")
        controls._settings_changed()
        assert settings[-1].threshold_source == "otsu"
        assert settings[-1].manual_threshold == 42
        assert str(controls.threshold_spin.cget("state")) == "disabled"
    finally:
        root.destroy()


def test_histogram_marks_hue_unavailable_in_grayscale_mode():
    tkinter = pytest.importorskip("tkinter")
    root = _root(tkinter)
    try:
        panel = HSVHistogramPanel(root)
        panel.set_grayscale_mode(True, threshold=128, polarity="bright")
        assert "unavailable" in panel.hue_note.lower()
        assert "Intensity" in panel.axis_labels["v"].get()
        assert "> 128" in panel.axis_labels["v"].get()
    finally:
        root.destroy()
