"""Six validated, synchronized HSV numeric controls."""

import re
import tkinter as tk
from tkinter import ttk

from ..errors import ValidationError
from ..models import HSVThresholdSet, THRESHOLD_FIELDS
from ..processing.thresholds import validate_thresholds


FIELD_SPECS = (
    ("lower_h_deg", "Lower H (°)", 0, 359),
    ("upper_h_deg", "Upper H (°)", 0, 360),
    ("lower_s_pct", "Lower S (%)", 0, 100),
    ("upper_s_pct", "Upper S (%)", 0, 100),
    ("lower_v_pct", "Lower V (%)", 0, 100),
    ("upper_v_pct", "Upper V (%)", 0, 100),
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
        self._spinboxes = []

        for column, (name, label, minimum, maximum) in enumerate(FIELD_SPECS):
            group = ttk.Frame(self)
            group.grid(row=0, column=column, padx=4, sticky="ew")
            self.columnconfigure(column, weight=1)
            ttk.Label(group, text=f"{label}\n{minimum}..{maximum}", anchor="center").pack()
            variable = tk.StringVar(value=str(getattr(self._last_valid, name)))
            spinbox = ttk.Spinbox(
                group, from_=minimum, to=maximum, increment=1, width=8,
                textvariable=variable, command=self._schedule_validation,
            )
            spinbox.pack(fill="x")
            variable.trace_add("write", self._schedule_validation)
            self.fields[name] = variable
            self._spinboxes.append(spinbox)

        self.range_text = (
            "H: lower 0..359°, upper 0..360°; lower > upper wraps through 0°. "
            "S and V: 0..100%, with lower ≤ upper."
        )
        ttk.Label(self, text=self.range_text, wraplength=900).grid(
            row=1, column=0, columnspan=6, sticky="w", pady=(6, 0)
        )
        self._error_var = tk.StringVar(value="")
        self._error_label = ttk.Label(self, textvariable=self._error_var, foreground="#a00000")
        self._error_label.grid(row=2, column=0, columnspan=6, sticky="w")

    @property
    def error_text(self) -> str:
        return self._error_var.get()

    def _schedule_validation(self, *_args) -> None:
        if self._updating:
            return
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        self._after_id = self.after(self._debounce_ms, self.validate_now)

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
                self._error_var.set("")
                if had_error and self._on_valid is not None:
                    self._on_valid(self._last_valid)
                return self._last_valid
            candidate = HSVThresholdSet(
                **candidate.as_dict(),
                parameter_revision=self._last_valid.parameter_revision + 1,
            )
        except ValidationError as error:
            self._error_var.set(str(error))
            if self._on_invalid is not None:
                self._on_invalid(error)
            return None

        self._last_valid = candidate
        self._error_var.set("")
        if self._on_valid is not None:
            self._on_valid(candidate)
        return candidate

    def set_thresholds(self, thresholds: HSVThresholdSet) -> None:
        self._updating = True
        try:
            for name in THRESHOLD_FIELDS:
                self.fields[name].set(str(getattr(thresholds, name)))
            self._last_valid = thresholds
            self._error_var.set("")
        finally:
            self._updating = False

    def set_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for spinbox in self._spinboxes:
            spinbox.configure(state=state)

    def destroy(self) -> None:
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
        super().destroy()
