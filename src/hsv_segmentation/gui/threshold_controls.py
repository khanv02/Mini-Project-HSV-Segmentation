"""Six validated, synchronized HSV numeric controls."""

import re
import tkinter as tk
from tkinter import ttk

from ..errors import ValidationError
from ..models import HSVThresholdSet, THRESHOLD_FIELDS
from ..processing.thresholds import validate_thresholds
from ..processing.threshold_suggestions import HSV_PRESETS
from .tooltips import ToolTip


FIELD_SPECS = (
    ("lower_h_deg", "Lower Hue (°)", 0, 359),
    ("upper_h_deg", "Upper Hue (°)", 0, 360),
    ("lower_s_pct", "Lower Saturation (%)", 0, 100),
    ("upper_s_pct", "Upper Saturation (%)", 0, 100),
    ("lower_v_pct", "Lower Value (%)", 0, 100),
    ("upper_v_pct", "Upper Value (%)", 0, 100),
)

FIELD_HELP = {
    "lower_h_deg": "Start of the accepted color angle. A value above Upper Hue wraps through 0°.",
    "upper_h_deg": "End of the accepted color angle. 0° is red, 120° green, 240° blue.",
    "lower_s_pct": "Minimum color intensity. Low saturation appears gray or washed out.",
    "upper_s_pct": "Maximum color intensity. Saturation bounds must stay in ascending order.",
    "lower_v_pct": "Minimum brightness. 0% is black and 100% is brightest.",
    "upper_v_pct": "Maximum brightness. Value bounds must stay in ascending order.",
}


def _format_selected_hsv(thresholds: HSVThresholdSet) -> str:
    return (
        f"Selected HSV: H [{thresholds.lower_h_deg}°, {thresholds.upper_h_deg}°], "
        f"S [{thresholds.lower_s_pct}%, {thresholds.upper_s_pct}%], "
        f"V [{thresholds.lower_v_pct}%, {thresholds.upper_v_pct}%]"
    )


class ThresholdControls(ttk.Frame):
    """Parse text separately from the pure typed threshold validator."""

    def __init__(
        self, master, *, on_valid=None, on_invalid=None,
        initial: HSVThresholdSet | None = None,
        debounce_ms: int = 75,
    ):
        super().__init__(master)
        self.pack(fill="x", expand=True)
        self._on_valid = on_valid
        self._on_invalid = on_invalid
        self._debounce_ms = debounce_ms
        self._after_id = None
        self._updating = False
        self._last_valid = initial or HSVThresholdSet()
        self.fields: dict[str, tk.StringVar] = {}
        self.sliders: dict[str, ttk.Scale] = {}
        self._slider_vars: dict[str, tk.DoubleVar] = {}
        self._spinboxes = []
        self._tooltips: list[ToolTip] = []
        self.layout_orientation = "horizontal"
        self.channel_groups: dict[str, ttk.LabelFrame] = {}
        for column in range(3):
            self.columnconfigure(column, weight=1, uniform="hsv-channel")

        channel_specs = (
            ("h", "Hue", "°", FIELD_SPECS[0:2]),
            ("s", "Saturation", "%", FIELD_SPECS[2:4]),
            ("v", "Value", "%", FIELD_SPECS[4:6]),
        )
        for column, (channel, title, unit, specs) in enumerate(channel_specs):
            channel_group = ttk.LabelFrame(self, text=f"{title} ({unit})", padding=4)
            channel_group.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0, 6) if column < 2 else 0,
            )
            channel_group.columnconfigure(0, weight=1)
            channel_group.columnconfigure(1, weight=1)
            self.channel_groups[channel] = channel_group
            for column, (name, _label, minimum, maximum) in enumerate(specs):
                bound = "Lower" if name.startswith("lower") else "Upper"
                group = ttk.Frame(channel_group)
                group.grid(
                    row=0, column=column, padx=(0, 4) if column == 0 else (4, 0),
                    sticky="ew",
                )
                header = ttk.Frame(group)
                header.pack(fill="x")
                label_widget = ttk.Label(header, text=bound, style="Muted.TLabel")
                label_widget.pack(side="left")
                variable = tk.StringVar(value=str(getattr(self._last_valid, name)))
                spinbox = ttk.Spinbox(
                    header, from_=minimum, to=maximum, increment=1, width=5,
                    textvariable=variable, command=self._schedule_validation,
                )
                spinbox.pack(side="right")
                slider_variable = tk.DoubleVar(value=getattr(self._last_valid, name))
                slider = ttk.Scale(
                    group,
                    from_=minimum,
                    to=maximum,
                    variable=slider_variable,
                    command=lambda value, selected=name: self._on_slider(selected, value),
                )
                slider.pack(fill="x", pady=(2, 0))
                variable.trace_add(
                    "write", lambda *_args, selected=name: self._on_field_changed(selected)
                )
                self.fields[name] = variable
                self._slider_vars[name] = slider_variable
                self.sliders[name] = slider
                self._spinboxes.append(spinbox)
                help_text = FIELD_HELP[name]
                self._tooltips.extend((
                    ToolTip(label_widget, help_text),
                    ToolTip(spinbox, help_text),
                    ToolTip(slider, f"Drag to change {bound.lower()} {title.lower()}. {help_text}"),
                ))

        actions = ttk.Frame(self)
        actions.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        ttk.Label(actions, text="Preset", style="Muted.TLabel").pack(side="left")
        self._preset_var = tk.StringVar(value="Custom")
        self._preset_box = ttk.Combobox(
            actions,
            textvariable=self._preset_var,
            values=("Custom", "Red", "Yellow", "Green", "Blue"),
            state="readonly",
            width=12,
        )
        self._preset_box.pack(side="left", padx=(5, 4), fill="x", expand=True)
        self._preset_box.bind("<<ComboboxSelected>>", self._on_preset_selected)
        self._reset_button = ttk.Button(actions, text="Reset", command=self.reset)
        self._reset_button.pack(side="left", padx=(4, 0))
        self._tooltips.extend((
            ToolTip(self._preset_box, "Apply a practical starting range for a common color."),
            ToolTip(self._reset_button, "Reset HSV thresholds to include every color and brightness."),
        ))

        self.range_text = "Hue range: 0–360° | Saturation: 0–100% | Value: 0–100%"
        self.explanation_text = (
            "Hue selects the color family; Saturation controls color intensity; "
            "Value controls brightness. Lower Hue above Upper Hue selects across 0°."
        )
        self._selected_var = tk.StringVar(value=_format_selected_hsv(self._last_valid))
        self._error_var = tk.StringVar(value="")
        self._error_label = ttk.Label(
            self, textvariable=self._error_var, style="Error.TLabel", wraplength=900
        )
        self._error_label.grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(4, 0)
        )
        self._error_label.grid_remove()

    @property
    def error_text(self) -> str:
        return self._error_var.get()

    @property
    def selected_text(self) -> str:
        return self._selected_var.get()

    @property
    def preset_name(self) -> str:
        return self._preset_var.get()

    def _on_field_changed(self, name: str) -> None:
        if self._updating:
            return
        self._preset_var.set("Custom")
        text = self.fields[name].get().strip()
        spec = next(item for item in FIELD_SPECS if item[0] == name)
        minimum, maximum = spec[2], spec[3]
        if re.fullmatch(r"[+-]?\d+", text):
            value = int(text)
            if minimum <= value <= maximum:
                self._updating = True
                try:
                    self._slider_vars[name].set(value)
                finally:
                    self._updating = False
        self._schedule_validation()

    def _on_slider(self, name: str, value: str) -> None:
        if self._updating:
            return
        rounded = round(float(value))
        if self.fields[name].get() != str(rounded):
            self.fields[name].set(str(rounded))

    def _on_preset_selected(self, _event=None) -> None:
        name = self._preset_var.get()
        if name != "Custom":
            self.apply_preset(name)

    def apply_preset(self, name: str) -> HSVThresholdSet | None:
        if name not in HSV_PRESETS:
            raise ValueError(f"unknown HSV preset: {name}")
        self._preset_var.set(name)
        return self.apply_thresholds(HSV_PRESETS[name])

    def reset(self) -> HSVThresholdSet | None:
        self._preset_var.set("Custom")
        return self.apply_thresholds(HSVThresholdSet())

    def apply_thresholds(self, thresholds: HSVThresholdSet) -> HSVThresholdSet | None:
        """Apply a user action through the same validation and callback path as edits."""
        self._updating = True
        try:
            for name in THRESHOLD_FIELDS:
                value = getattr(thresholds, name)
                self.fields[name].set(str(value))
                self._slider_vars[name].set(value)
        finally:
            self._updating = False
        return self.validate_now()

    def _schedule_validation(self, *_args) -> None:
        if self._updating:
            return
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        self._after_id = self.after(self._debounce_ms, self.validate_now)

    def _set_error(self, text: str) -> None:
        self._error_var.set(text)
        if text:
            self._error_label.grid()
        else:
            self._error_label.grid_remove()

    def validate_now(self) -> HSVThresholdSet | None:
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except tk.TclError:
                pass
        self._after_id = None
        values = {}
        had_error = bool(self._error_var.get())
        try:
            ranges = {name: (minimum, maximum) for name, _label, minimum, maximum in FIELD_SPECS}
            for name in THRESHOLD_FIELDS:
                text = self.fields[name].get().strip()
                if re.fullmatch(r"[+-]?\d+", text) is None:
                    minimum, maximum = ranges[name]
                    raise ValidationError(
                        name, f"must be a whole number in {minimum}..{maximum}"
                    )
                values[name] = int(text)
            candidate = validate_thresholds(values)
            if candidate.as_dict() == self._last_valid.as_dict():
                self._set_error("")
                if had_error and self._on_valid is not None:
                    self._on_valid(self._last_valid)
                return self._last_valid
            candidate = HSVThresholdSet(
                **candidate.as_dict(),
                parameter_revision=self._last_valid.parameter_revision + 1,
            )
        except ValidationError as error:
            self._set_error(str(error))
            if self._on_invalid is not None:
                self._on_invalid(error)
            return None

        self._last_valid = candidate
        self._selected_var.set(_format_selected_hsv(candidate))
        self._set_error("")
        if self._on_valid is not None:
            self._on_valid(candidate)
        return candidate

    def set_thresholds(self, thresholds: HSVThresholdSet) -> None:
        self._updating = True
        try:
            for name in THRESHOLD_FIELDS:
                value = getattr(thresholds, name)
                self.fields[name].set(str(value))
                self._slider_vars[name].set(value)
            self._last_valid = thresholds
            self._selected_var.set(_format_selected_hsv(thresholds))
            self._set_error("")
        finally:
            self._updating = False

    def set_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for spinbox in self._spinboxes:
            spinbox.configure(state=state)
        for slider in self.sliders.values():
            slider.configure(state=state)
        self._preset_box.configure(state="readonly" if enabled else "disabled")
        self._reset_button.configure(state=state)

    def destroy(self) -> None:
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
        super().destroy()
