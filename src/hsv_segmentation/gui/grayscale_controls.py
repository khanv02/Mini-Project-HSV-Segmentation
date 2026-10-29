"""Compact explicit controls for opt-in grayscale intensity segmentation."""

import tkinter as tk
from tkinter import ttk

from ..models import GrayscaleSettings, SegmentationMode


class GrayscaleControls(ttk.Frame):
    """Emit mode/settings snapshots; never infer or switch modes automatically."""

    def __init__(self, master, *, on_mode=None, on_settings=None):
        super().__init__(master)
        self.pack(side="left", padx=(8, 0))
        self._on_mode = on_mode
        self._on_settings = on_settings
        self._updating = False
        self._eligible = False
        self._settings_revision = 0

        self.mode_var = tk.StringVar(value="HSV")
        self.mode_box = ttk.Combobox(
            self, textvariable=self.mode_var, values=("HSV", "Grayscale"),
            state="readonly", width=11,
        )
        self.mode_box.grid(row=0, column=0, padx=(0, 6), sticky="w")
        self.mode_box.bind("<<ComboboxSelected>>", self._mode_changed)

        self.source_var = tk.StringVar(value="Manual")
        self.source_box = ttk.Combobox(
            self, textvariable=self.source_var, values=("Manual", "Otsu"),
            state="disabled", width=8,
        )
        self.source_box.grid(row=0, column=1, padx=(0, 6))
        self.source_box.bind("<<ComboboxSelected>>", self._settings_changed)

        self.threshold_var = tk.IntVar(value=128)
        self.threshold_spin = ttk.Spinbox(
            self, from_=0, to=255, textvariable=self.threshold_var, width=5,
            state="disabled", command=self._settings_changed,
        )
        self.threshold_spin.grid(row=0, column=2, padx=(0, 6))
        self.threshold_spin.bind("<Return>", self._settings_changed)
        self.threshold_spin.bind("<FocusOut>", self._settings_changed)

        self.polarity_var = tk.StringVar(value="Bright > T")
        self.polarity_box = ttk.Combobox(
            self, textvariable=self.polarity_var,
            values=("Bright > T", "Dark <= T"), state="disabled", width=12,
        )
        self.polarity_box.grid(row=0, column=3, padx=(0, 8))
        self.polarity_box.bind("<<ComboboxSelected>>", self._settings_changed)

        self.status_var = tk.StringVar(value="Open a source; HSV is the default.")
        self.status_label = ttk.Label(self, textvariable=self.status_var, style="Muted.TLabel")
        self.status_label.grid(
            row=0, column=4, sticky="w"
        )
        self.columnconfigure(4, weight=1)

    @property
    def mode(self) -> SegmentationMode:
        return (
            SegmentationMode.GRAYSCALE
            if self.mode_var.get() == "Grayscale"
            else SegmentationMode.HSV
        )

    @property
    def settings(self) -> GrayscaleSettings:
        return GrayscaleSettings(
            threshold_source=self.source_var.get().lower(),
            manual_threshold=int(self.threshold_var.get()),
            polarity=(
                "bright" if self.polarity_var.get().startswith("Bright") else "dark"
            ),
            settings_revision=self._settings_revision,
        )

    def set_source_eligibility(self, eligible: bool, reason: str | None = None) -> None:
        self._eligible = bool(eligible)
        if self.mode is SegmentationMode.HSV:
            self.status_var.set(
                "Grayscale available (opt-in)."
                if eligible
                else (reason or "Source is not exact grayscale.")
            )
        self._refresh_states()

    def reset_for_source(self, eligible: bool, reason: str | None = None) -> None:
        self._updating = True
        try:
            self.mode_var.set("HSV")
            self.source_var.set("Manual")
        finally:
            self._updating = False
        self.set_source_eligibility(eligible, reason)

    def show_result(self, result) -> None:
        self._updating = True
        try:
            self.mode_var.set(
                "Grayscale" if result.segmentation_mode == "grayscale" else "HSV"
            )
            self.source_var.set(result.grayscale_settings.threshold_source.title())
            self.threshold_var.set(result.grayscale_settings.manual_threshold)
            self.polarity_var.set(
                "Bright > T"
                if result.grayscale_settings.polarity == "bright"
                else "Dark <= T"
            )
            self._settings_revision = result.grayscale_settings.settings_revision
            eligibility = result.grayscale_eligibility
            self._eligible = bool(eligibility and eligibility.eligible)
            if result.segmentation_mode == "grayscale":
                if result.otsu_outcome.status == "applied":
                    self.status_var.set(f"Otsu threshold: {result.otsu_outcome.threshold}")
                else:
                    self.status_var.set("Intensity is active; Hue is not meaningful.")
            else:
                self.status_var.set(
                    "Grayscale available (opt-in)." if self._eligible else "HSV mode"
                )
        finally:
            self._updating = False
        self._refresh_states()

    def reject_mode(self, reason: str) -> None:
        self._updating = True
        try:
            self.mode_var.set("HSV")
        finally:
            self._updating = False
        self.status_var.set(reason)
        self._refresh_states()

    def _mode_changed(self, _event=None) -> None:
        if self._updating:
            return
        if self.mode is SegmentationMode.GRAYSCALE and not self._eligible:
            self.reject_mode("Source is not exact grayscale; HSV result preserved.")
            return
        self._refresh_states()
        if self._on_mode:
            self._on_mode(self.mode)

    def _settings_changed(self, _event=None) -> None:
        if self._updating or self.mode is not SegmentationMode.GRAYSCALE:
            return
        self._settings_revision += 1
        self._refresh_states()
        if self._on_settings:
            self._on_settings(self.settings)

    def _refresh_states(self) -> None:
        active = self.mode is SegmentationMode.GRAYSCALE and self._eligible
        self.source_box.configure(state="readonly" if active else "disabled")
        self.polarity_box.configure(state="readonly" if active else "disabled")
        manual = active and self.source_var.get() == "Manual"
        self.threshold_spin.configure(state="normal" if manual else "disabled")
