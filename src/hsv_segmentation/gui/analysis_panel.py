"""Compact controls and statistics for optional object analysis and evaluation."""

import tkinter as tk
from tkinter import ttk

from ..errors import ValidationError
from ..models import AnalysisSettings, SegmentationResult, WatershedSettings


class AnalysisPanel(ttk.LabelFrame):
    def __init__(self, master, *, on_settings, on_display, on_load_truth, on_clear_truth):
        super().__init__(master, text="Object Analysis & Evaluation", padding=6)
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

        row = ttk.Frame(self); row.pack(fill="x")
        ttk.Checkbutton(row, text="Analyze regions", variable=self.enabled_var,
                        command=self._emit).pack(side="left")
        ttk.Label(row, text="Neighbors").pack(side="left", padx=(8, 2))
        box = ttk.Combobox(row, textvariable=self.connectivity_var,
                           values=("4", "8"), width=3, state="readonly")
        box.pack(side="left"); box.bind("<<ComboboxSelected>>", lambda _e: self._emit())
        area = ttk.Frame(self); area.pack(fill="x", pady=(3, 0))
        ttk.Label(area, text="Minimum area (source px)").pack(side="left")
        entry = ttk.Entry(area, textvariable=self.min_area_var, width=7); entry.pack(side="left", padx=(4, 0))
        entry.bind("<Return>", lambda _e: self._emit()); entry.bind("<FocusOut>", lambda _e: self._emit())

        water = ttk.Frame(self); water.pack(fill="x", pady=(4, 0))
        ttk.Checkbutton(water, text="Watershed", variable=self.watershed_var,
                        command=self._emit).pack(side="left")
        ttk.Label(water, text="Seed fraction").pack(side="left", padx=(8, 2))
        seed = ttk.Entry(water, textvariable=self.seed_var, width=6); seed.pack(side="left")
        seed.bind("<Return>", lambda _e: self._emit()); seed.bind("<FocusOut>", lambda _e: self._emit())
        display = ttk.Frame(self); display.pack(fill="x", pady=(3, 0))
        ttk.Checkbutton(display, text="Contours", variable=self.contours_var,
                        command=self._display).pack(side="left")
        ttk.Checkbutton(display, text="Boxes", variable=self.boxes_var,
                        command=self._display).pack(side="left")
        ttk.Checkbutton(display, text="TP/FP/FN", variable=self.confusion_var,
                        command=self._display).pack(side="left")

        evaluation = ttk.Frame(self); evaluation.pack(fill="x", pady=(4, 0))
        ttk.Label(evaluation, text="Evaluate").pack(side="left")
        targets = ttk.Combobox(evaluation, textvariable=self.target_var,
                               values=("baseline", "components", "watershed"),
                               width=11, state="readonly")
        targets.pack(side="left", padx=(3, 5)); targets.bind("<<ComboboxSelected>>", lambda _e: self._emit())
        truth = ttk.Frame(self); truth.pack(fill="x", pady=(3, 0))
        ttk.Label(truth, text="Truth >").pack(side="left")
        ttk.Entry(truth, textvariable=self.truth_threshold_var, width=4).pack(side="left")
        ttk.Button(truth, text="Load…", width=6, command=self._load).pack(side="left", padx=(4, 0))
        ttk.Button(truth, text="Clear", width=6, command=on_clear_truth).pack(side="left", padx=(3, 0))

        ttk.Label(self, textvariable=self.summary_var).pack(anchor="w", pady=(4, 0))
        ttk.Label(self, textvariable=self.truth_var).pack(anchor="w")
        ttk.Label(self, textvariable=self.metrics_var).pack(anchor="w")
        self.tree = ttk.Treeview(self, columns=("area", "centroid", "box"), show="headings", height=3)
        for key, title, width in (("area", "Area px", 55), ("centroid", "Centroid", 85), ("box", "Box x,y,w,h", 95)):
            self.tree.heading(key, text=title); self.tree.column(key, width=width, stretch=True)
        self.tree.pack(fill="x", pady=(4, 0))

    def _values(self):
        try:
            analysis = AnalysisSettings(
                self.enabled_var.get(), int(self.connectivity_var.get()), int(self.min_area_var.get())
            )
            watershed = WatershedSettings(
                self.watershed_var.get(), float(self.seed_var.get()), 1, 3
            )
        except (ValueError, ValidationError) as error:
            self.summary_var.set(f"Invalid analysis setting: {error}")
            return None
        return analysis, watershed, self.target_var.get()

    def _emit(self):
        values = self._values()
        if values is not None:
            self._on_settings(*values)

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
                self.tree.insert("", "end", values=(
                    region.area_px,
                    f"{region.centroid_x:.1f}, {region.centroid_y:.1f}",
                    ", ".join(str(v) for v in region.box),
                ))
        if result.watershed is not None:
            suffix = result.watershed.status.replace("_", " ")
            if result.watershed.reason:
                suffix += f": {result.watershed.reason}"
            self.summary_var.set(self.summary_var.get() + f" | Watershed {suffix}")
        truth = result.ground_truth
        self.truth_var.set("Ground truth: —" if truth is None else
                           f"Ground truth: {truth.source_path.name}, values > {truth.threshold}")
        metric = result.evaluation
        self.metrics_var.set("IoU: —   Dice: —" if metric is None else
                             f"IoU: {metric.iou:.4f}   Dice: {metric.dice:.4f} ({metric.status})")
