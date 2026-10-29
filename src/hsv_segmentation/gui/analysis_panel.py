"""Compact controls and statistics for optional object analysis and evaluation."""

import tkinter as tk
from tkinter import ttk

from ..errors import ValidationError
from ..models import AnalysisSettings, SegmentationResult, WatershedSettings


class AnalysisPanel(ttk.Frame):
    def __init__(self, master, *, on_settings, on_display, on_load_truth, on_clear_truth):
        super().__init__(master)
        self._on_settings = on_settings
        self._on_display = on_display
        self._on_load_truth = on_load_truth
        self._on_clear_truth = on_clear_truth
        self.enabled_var = tk.BooleanVar(value=False)
        self.connectivity_var = tk.StringVar(value="8")
        self.min_area_var = tk.StringVar(value="0")
        self.watershed_var = tk.BooleanVar(value=False)
        self.seed_var = tk.StringVar(value="0.5")
        self.target_var = tk.StringVar(value="baseline")
        self.contours_var = tk.BooleanVar(value=True)
        self.boxes_var = tk.BooleanVar(value=True)
        self.confusion_var = tk.BooleanVar(value=False)
        self.truth_threshold_var = tk.StringVar(value="0")
        self.summary_var = tk.StringVar(value="Analysis disabled")
        self.metrics_var = tk.StringVar(value="IoU: —   Dice: —")
        self.truth_var = tk.StringVar(value="Ground truth: —")

        for column in range(4):
            self.columnconfigure(column, weight=1)
        self.rowconfigure(0, weight=1)

        regions = ttk.Frame(self, padding=(0, 0, 8, 0))
        regions.grid(row=0, column=0, sticky="nsew")
        ttk.Label(regions, text="OBJECTS", style="Eyebrow.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        ttk.Checkbutton(
            regions,
            text="Enable object analysis",
            variable=self.enabled_var,
            command=self._emit,
        ).grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Label(regions, text="Connectivity", style="Muted.TLabel").grid(
            row=2, column=0, sticky="w", pady=(6, 2)
        )
        ttk.Label(regions, text="Minimum area (px)", style="Muted.TLabel").grid(
            row=2, column=1, sticky="w", padx=(8, 0), pady=(6, 2)
        )
        self.connectivity_box = ttk.Combobox(
            regions,
            textvariable=self.connectivity_var,
            values=("4", "8"),
            width=8,
            state="readonly",
        )
        self.connectivity_box.grid(row=3, column=0, sticky="ew")
        self.connectivity_box.bind("<<ComboboxSelected>>", lambda _event: self._emit())
        self.min_area_entry = ttk.Entry(regions, textvariable=self.min_area_var, width=12)
        self.min_area_entry.grid(row=3, column=1, sticky="ew", padx=(8, 0))
        self.min_area_entry.bind("<Return>", lambda _event: self._emit())
        self.min_area_entry.bind("<FocusOut>", lambda _event: self._emit())
        regions.columnconfigure(0, weight=1)
        regions.columnconfigure(1, weight=1)

        separation = ttk.Frame(self, padding=(8, 0))
        separation.grid(row=0, column=1, sticky="nsew")
        ttk.Label(
            separation, text="SEPARATION & OVERLAY", style="Eyebrow.TLabel"
        ).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )
        ttk.Checkbutton(
            separation,
            text="Enable Watershed",
            variable=self.watershed_var,
            command=self._emit,
        ).grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Label(separation, text="Seed", style="Muted.TLabel").grid(
            row=1, column=2, sticky="e", padx=(8, 2)
        )
        self.seed_entry = ttk.Entry(separation, textvariable=self.seed_var, width=6)
        self.seed_entry.grid(row=2, column=2, sticky="e", pady=(4, 0))
        self.seed_entry.bind("<Return>", lambda _event: self._emit())
        self.seed_entry.bind("<FocusOut>", lambda _event: self._emit())
        self.contours_button = ttk.Checkbutton(
            separation, text="Contours", variable=self.contours_var, command=self._display
        )
        self.contours_button.grid(row=2, column=0, sticky="w", pady=(4, 0))
        self.boxes_button = ttk.Checkbutton(
            separation, text="Boxes", variable=self.boxes_var, command=self._display
        )
        self.boxes_button.grid(row=2, column=1, sticky="w", pady=(4, 0))
        self.confusion_button = ttk.Checkbutton(
            separation, text="TP/FP/FN", variable=self.confusion_var, command=self._display
        )
        self.confusion_button.grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )
        separation.columnconfigure(0, weight=1)

        evaluation = ttk.Frame(self, padding=(8, 0))
        evaluation.grid(row=0, column=2, sticky="nsew")
        ttk.Label(
            evaluation, text="GROUND-TRUTH EVALUATION", style="Eyebrow.TLabel"
        ).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 4)
        )
        ttk.Label(evaluation, text="Target", style="Muted.TLabel").grid(
            row=1, column=0, sticky="w"
        )
        ttk.Label(evaluation, text="Threshold >", style="Muted.TLabel").grid(
            row=1, column=1, sticky="w", padx=(8, 0)
        )
        self.target_box = ttk.Combobox(
            evaluation,
            textvariable=self.target_var,
            values=("baseline", "components", "watershed"),
            width=10,
            state="readonly",
        )
        self.target_box.grid(row=2, column=0, sticky="ew")
        self.target_box.bind("<<ComboboxSelected>>", lambda _event: self._emit())
        self.truth_threshold_entry = ttk.Entry(
            evaluation, textvariable=self.truth_threshold_var, width=4
        )
        self.truth_threshold_entry.grid(row=2, column=1, sticky="ew", padx=(8, 0))
        ttk.Button(evaluation, text="Load", width=4, command=self._load).grid(
            row=2, column=2, padx=(6, 0)
        )
        ttk.Button(evaluation, text="Clear", width=4, command=self._on_clear_truth).grid(
            row=2, column=3, padx=(4, 0)
        )
        evaluation.columnconfigure(0, weight=1)
        evaluation.columnconfigure(1, weight=1)
        metrics_row = ttk.Frame(evaluation)
        metrics_row.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        ttk.Label(
            metrics_row, textvariable=self.truth_var, style="Muted.TLabel"
        ).pack(side="left")
        ttk.Label(
            metrics_row, textvariable=self.metrics_var, style="Metric.TLabel"
        ).pack(side="right")

        statistics = ttk.Frame(self, padding=(8, 0, 0, 0))
        statistics.grid(row=0, column=3, sticky="nsew")
        statistics.columnconfigure(0, weight=1)
        statistics.rowconfigure(1, weight=1)
        results_header = ttk.Frame(statistics)
        results_header.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ttk.Label(results_header, text="OBJECT STATISTICS", style="Eyebrow.TLabel").pack(
            side="left"
        )
        ttk.Label(results_header, textvariable=self.summary_var, style="Muted.TLabel").pack(
            side="right"
        )
        self.tree = ttk.Treeview(
            statistics, columns=("area", "centroid", "box"), show="headings", height=3
        )
        for key, title, width in (
            ("area", "Area px", 55),
            ("centroid", "Centroid", 85),
            ("box", "Box x,y,w,h", 95),
        ):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, stretch=True)
        self.tree.grid(row=1, column=0, sticky="nsew")
        self._refresh_states()

    def _values(self):
        try:
            analysis = AnalysisSettings(
                self.enabled_var.get(),
                int(self.connectivity_var.get()),
                int(self.min_area_var.get()),
            )
            watershed = WatershedSettings(
                self.watershed_var.get(), float(self.seed_var.get()), 1, 3
            )
        except (ValueError, ValidationError) as error:
            self.summary_var.set(f"Invalid analysis setting: {error}")
            return None
        return analysis, watershed, self.target_var.get()

    def _emit(self):
        self._refresh_states()
        values = self._values()
        if values is not None:
            self._on_settings(*values)

    def _refresh_states(self):
        analysis_state = "readonly" if self.enabled_var.get() else "disabled"
        entry_state = "normal" if self.enabled_var.get() else "disabled"
        overlay_state = (
            "normal"
            if self.enabled_var.get() or self.watershed_var.get()
            else "disabled"
        )
        self.connectivity_box.configure(state=analysis_state)
        self.min_area_entry.configure(state=entry_state)
        self.seed_entry.configure(state="normal" if self.watershed_var.get() else "disabled")
        self.contours_button.configure(state=overlay_state)
        self.boxes_button.configure(state=overlay_state)

    def _display(self):
        self._on_display(self.contours_var.get(), self.boxes_var.get(), self.confusion_var.get())

    def _load(self):
        try:
            threshold = int(self.truth_threshold_var.get())
            if not 0 <= threshold <= 254:
                raise ValueError
        except ValueError:
            self.truth_var.set("Truth threshold must be an integer in 0..254")
            return
        self._on_load_truth(threshold)

    def show_result(self, result: SegmentationResult) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        analysis = result.analysis
        if analysis is None:
            self.summary_var.set("Analysis disabled")
        else:
            self.summary_var.set(
                f"Connected regions: {analysis.retained_count} retained / {analysis.raw_count} raw"
            )
            for region in analysis.regions:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        region.area_px,
                        f"{region.centroid_x:.1f}, {region.centroid_y:.1f}",
                        ", ".join(str(value) for value in region.box),
                    ),
                )
        if result.watershed is not None:
            suffix = result.watershed.status.replace("_", " ")
            if result.watershed.reason:
                suffix += f": {result.watershed.reason}"
            self.summary_var.set(self.summary_var.get() + f" | Watershed {suffix}")
        truth = result.ground_truth
        self.truth_var.set(
            "Ground truth: —"
            if truth is None
            else f"Ground truth: {truth.source_path.name}, values > {truth.threshold}"
        )
        metric = result.evaluation
        self.metrics_var.set(
            "IoU: —   Dice: —"
            if metric is None
            else f"IoU: {metric.iou:.4f}   Dice: {metric.dice:.4f} ({metric.status})"
        )
