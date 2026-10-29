"""Compact controls for optional mask post-processing."""

import tkinter as tk
from tkinter import ttk

from ..models import MorphologySettings
from .tooltips import ToolTip


OPERATION_LABELS = {
    "Opening": "opening",
    "Closing": "closing",
    "Opening → Closing": "opening_closing",
}
OPERATION_NAMES = {value: label for label, value in OPERATION_LABELS.items()}


class MorphologyControls(ttk.Frame):
    """Emit immutable settings while keeping the feature disabled by default."""

    def __init__(self, master, *, initial=None, on_change=None):
        super().__init__(master)
        self.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self._on_change = on_change
        self._application_enabled = True
        self._updating = False
        settings = initial or MorphologySettings()

        self.enabled_var = tk.BooleanVar(value=settings.enabled)
        self.enable_button = ttk.Checkbutton(
            self,
            text="Enable Morphology",
            variable=self.enabled_var,
            command=self._changed,
        )
        self.enable_button.grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(self, text="Operation", style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", pady=(6, 2), padx=(0, 4)
        )
        self.operation_var = tk.StringVar(value=OPERATION_NAMES[settings.operation])
        self.operation_box = ttk.Combobox(
            self,
            textvariable=self.operation_var,
            values=tuple(OPERATION_LABELS),
            state="readonly",
            width=18,
        )
        self.operation_box.grid(row=2, column=0, sticky="ew", padx=(0, 4))
        self.operation_box.bind("<<ComboboxSelected>>", self._changed)

        ttk.Label(self, text="Square kernel", style="Muted.TLabel").grid(
            row=1, column=1, sticky="w", pady=(6, 2), padx=(4, 0)
        )
        self.kernel_var = tk.StringVar(value=f"{settings.kernel_size}×{settings.kernel_size}")
        kernel_group = ttk.Frame(self)
        kernel_group.grid(row=2, column=1, sticky="ew", padx=(4, 0))
        self.kernel_buttons = {}
        for size in (3, 5, 7, 9):
            label = f"{size}×{size}"
            button = ttk.Radiobutton(
                kernel_group,
                text=label,
                value=label,
                variable=self.kernel_var,
                command=self._changed,
            )
            button.pack(side="left", padx=(0, 5))
            self.kernel_buttons[size] = button
        self.explanation = ttk.Label(
            self,
            text="Opening removes specks; Closing fills holes; the combined mode runs in that order.",
        )
        self.explanation.configure(wraplength=270, style="Muted.TLabel")
        self.explanation.grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )
        self._tooltips = (
            ToolTip(
                self.enable_button,
                "Refine the current HSV or Grayscale selection mask before analysis and export.",
            ),
            ToolTip(
                self.operation_box,
                "Opening removes isolated foreground noise; Closing fills small background gaps.",
            ),
            *(ToolTip(
                button,
                "Apply this square neighborhood once; larger sizes affect larger features.",
            ) for button in self.kernel_buttons.values()),
        )
        self._refresh_states()

    @property
    def settings(self) -> MorphologySettings:
        kernel_size = int(self.kernel_var.get().split("×", 1)[0])
        return MorphologySettings(
            enabled=bool(self.enabled_var.get()),
            operation=OPERATION_LABELS[self.operation_var.get()],
            kernel_size=kernel_size,
        )

    def _changed(self, _event=None) -> None:
        if self._updating:
            return
        self._refresh_states()
        if self._on_change is not None:
            self._on_change(self.settings)

    def _refresh_states(self) -> None:
        feature_controls_enabled = self._application_enabled and self.enabled_var.get()
        self.enable_button.configure(
            state="normal" if self._application_enabled else "disabled"
        )
        state = "readonly" if feature_controls_enabled else "disabled"
        self.operation_box.configure(state=state)
        button_state = "normal" if feature_controls_enabled else "disabled"
        for button in self.kernel_buttons.values():
            button.configure(state=button_state)

    def set_settings(self, settings: MorphologySettings) -> None:
        self._updating = True
        try:
            self.enabled_var.set(settings.enabled)
            self.operation_var.set(OPERATION_NAMES[settings.operation])
            self.kernel_var.set(f"{settings.kernel_size}×{settings.kernel_size}")
        finally:
            self._updating = False
        self._refresh_states()

    def set_enabled(self, enabled: bool) -> None:
        self._application_enabled = bool(enabled)
        self._refresh_states()

