"""Compact controls for optional marker-controlled object separation."""

import tkinter as tk
from tkinter import ttk

from ..errors import ValidationError
from ..models import WatershedSettings


class WatershedControls(ttk.Frame):
    """Keep separation settings with mask-refinement controls, not analysis."""

    def __init__(self, master, *, initial=None, on_change=None):
        super().__init__(master, padding=(8, 0, 0, 0))
        self.pack(side="left", fill="both", expand=True)
        self._on_change = on_change
        self._application_enabled = True
        self._updating = False
        settings = initial or WatershedSettings()

        self.enabled_var = tk.BooleanVar(value=settings.enabled)
        self.seed_var = tk.StringVar(value=str(settings.seed_fraction))
        self.status_var = tk.StringVar(value="Separation disabled")

        self.enable_button = ttk.Checkbutton(
            self,
            text="Separate touching objects (Watershed)",
            variable=self.enabled_var,
            command=self._changed,
        )
        self.enable_button.grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(self, text="Seed fraction", style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", pady=(6, 2)
        )
        self.seed_entry = ttk.Entry(self, textvariable=self.seed_var, width=8)
        self.seed_entry.grid(row=2, column=0, sticky="w")
        self.seed_entry.bind("<Return>", self._changed)
        self.seed_entry.bind("<FocusOut>", self._changed)
        ttk.Label(
            self,
            text="Splits connected foreground regions after mask cleanup.",
            style="Muted.TLabel",
        ).grid(row=2, column=1, sticky="w", padx=(10, 0))
        ttk.Label(self, textvariable=self.status_var, style="Muted.TLabel").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )
        self.columnconfigure(1, weight=1)
        self._refresh_states()

    @property
    def settings(self) -> WatershedSettings:
        return WatershedSettings(
            enabled=bool(self.enabled_var.get()),
            seed_fraction=float(self.seed_var.get()),
            background_iterations=1,
            kernel_size=3,
        )

    def _changed(self, _event=None) -> None:
        if self._updating:
            return
        self._refresh_states()
        try:
            settings = self.settings
        except (ValueError, ValidationError) as error:
            self.status_var.set(f"Invalid Watershed setting: {error}")
            return
        self.status_var.set(
            "Separation enabled" if settings.enabled else "Separation disabled"
        )
        if self._on_change is not None:
            self._on_change(settings)

    def _refresh_states(self) -> None:
        enabled = self._application_enabled and self.enabled_var.get()
        self.enable_button.configure(
            state="normal" if self._application_enabled else "disabled"
        )
        self.seed_entry.configure(state="normal" if enabled else "disabled")

    def set_settings(self, settings: WatershedSettings) -> None:
        self._updating = True
        try:
            self.enabled_var.set(settings.enabled)
            self.seed_var.set(str(settings.seed_fraction))
        finally:
            self._updating = False
        self._refresh_states()

    def show_result(self, result) -> None:
        watershed = result.watershed
        if watershed is None:
            self.status_var.set("Separation disabled")
            return
        status = watershed.status.replace("_", " ")
        if watershed.reason:
            status += f": {watershed.reason}"
        self.status_var.set(f"Watershed {status}")

    def set_enabled(self, enabled: bool) -> None:
        self._application_enabled = bool(enabled)
        self._refresh_states()
