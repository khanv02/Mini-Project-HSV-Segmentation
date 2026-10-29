"""Regression tests for morphology control-to-settings events."""

import time

import pytest

from hsv_segmentation.gui.morphology_controls import MorphologyControls


def _root():
    tkinter = pytest.importorskip("tkinter")
    last_error = None
    for _ in range(3):
        try:
            root = tkinter.Tk()
            root.withdraw()
            return root
        except tkinter.TclError as error:
            last_error = error
            time.sleep(0.05)
    pytest.fail(f"Tk root could not be created: {last_error}")


def test_kernel_selection_immediately_emits_updated_settings() -> None:
    root = _root()
    emitted = []
    try:
        controls = MorphologyControls(root, on_change=emitted.append)
        controls.enable_button.invoke()
        root.update()
        emitted.clear()

        controls.kernel_buttons[5].invoke()
        root.update()

        assert len(emitted) == 1
        assert emitted[0].enabled is True
        assert emitted[0].operation == "opening"
        assert emitted[0].kernel_size == 5
    finally:
        root.destroy()


def test_combined_label_states_the_execution_order() -> None:
    root = _root()
    try:
        controls = MorphologyControls(root)
        assert "Opening → Closing" in controls.operation_box.cget("values")
        controls.operation_var.set("Opening → Closing")
        assert controls.settings.operation == "opening_closing"
    finally:
        root.destroy()


def test_each_kernel_size_is_a_direct_enabled_choice() -> None:
    root = _root()
    try:
        controls = MorphologyControls(root)
        assert tuple(controls.kernel_buttons) == (3, 5, 7, 9)
        assert all(
            str(button.cget("state")) == "disabled"
            for button in controls.kernel_buttons.values()
        )
        controls.enable_button.invoke()
        assert all(
            str(button.cget("state")) == "normal"
            for button in controls.kernel_buttons.values()
        )
    finally:
        root.destroy()
