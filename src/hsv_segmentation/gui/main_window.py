"""Top-level layout for the still-image MVP."""

import tkinter as tk
from tkinter import ttk

from ..models import SegmentationResult
from .experiment_panel import ExperimentPanel
from .hsv_histogram import HSVHistogramPanel
from .image_view import ImageView


class MainWindow:
    """Compose named sections and three synchronized result views."""

    def __init__(self, root: tk.Tk | None = None):
        self.root = root or tk.Tk()
        self._displayed_source_identity: tuple[str, int | None] | None = None
        self.root.title("HSV Color Segmentation")
        self.root.minsize(960, 640)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        initial_width = max(960, min(1400, screen_width - 80))
        initial_height = max(640, min(900, screen_height - 100))
        self.root.geometry(f"{initial_width}x{initial_height}")

        container = ttk.Frame(self.root, padding=10)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(3, weight=1)

        self.input_section = ttk.LabelFrame(container, text="File Input", padding=8)
        self.input_section.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.open_image_button = ttk.Button(self.input_section, text="Open Image…")
        self.open_image_button.pack(side="left")
        self.open_video_button = ttk.Button(self.input_section, text="Open Video…")
        self.open_video_button.pack(side="left", padx=(6, 0))
        self.save_mask_button = ttk.Button(
            self.input_section, text="Save Mask…", state="disabled"
        )
        self.save_mask_button.pack(side="left", padx=(18, 0))
        self.save_result_button = ttk.Button(
            self.input_section, text="Save Result…", state="disabled"
        )
        self.save_result_button.pack(side="left", padx=(6, 0))
        self.play_button = ttk.Button(self.input_section, text="Play", state="disabled")
        self.play_button.pack(side="left", padx=(18, 0))
        self.pause_button = ttk.Button(self.input_section, text="Pause", state="disabled")
        self.pause_button.pack(side="left", padx=(6, 0))
        self.restart_button = ttk.Button(self.input_section, text="Restart", state="disabled")
        self.restart_button.pack(side="left", padx=(6, 0))
        self.frame_var = tk.StringVar(value="Frame: —")
        ttk.Label(self.input_section, textvariable=self.frame_var).pack(
            side="left", padx=(12, 0)
        )
        self.source_label = ttk.Label(self.input_section, text="No image loaded")
        self.source_label.pack(side="left", padx=12)

        self.parameter_section = ttk.LabelFrame(container, text="HSV Parameters", padding=8)
        self.parameter_section.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.experiment_panel = ExperimentPanel(container)
        self.experiment_panel.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.record_experiment_button = self.experiment_panel.record_button

        self.visualization_section = ttk.LabelFrame(
            container, text="Result Visualization", padding=8
        )
        self.visualization_section.grid(row=3, column=0, sticky="nsew")
        for column in range(3):
            self.visualization_section.columnconfigure(column, weight=1, uniform="view")
        self.visualization_section.rowconfigure(1, weight=1)

        visualization_toolbar = ttk.Frame(self.visualization_section)
        visualization_toolbar.grid(row=0, column=0, columnspan=3, sticky="e", padx=4)
        self.histogram_toggle_button = ttk.Button(
            visualization_toolbar, text="Show Histogram", command=self.toggle_histogram
        )
        self.histogram_toggle_button.pack(side="right")

        self.original_view = ImageView(self.visualization_section, title="Original")
        self.mask_view = ImageView(
            self.visualization_section, title="Binary Mask", is_mask=True
        )
        self.result_view = ImageView(self.visualization_section, title="Segmented Result")
        self.views = (self.original_view, self.mask_view, self.result_view)
        for column, view in enumerate(self.views):
            view.grid(row=1, column=column, sticky="nsew", padx=4)

        self.histogram_panel = HSVHistogramPanel(self.visualization_section)
        self.histogram_panel.grid(
            row=2, column=0, columnspan=3, sticky="ew", padx=4, pady=(4, 0)
        )
        self.histogram_panel.grid_remove()
        self._histogram_visible = False

        self.status_var = tk.StringVar(value="Ready — open a PNG, JPEG, or BMP image.")
        ttk.Label(container, textvariable=self.status_var, anchor="w").grid(
            row=4, column=0, sticky="ew", pady=(8, 0)
        )

    def show_result(self, result: SegmentationResult) -> None:
        source_identity = (result.session_id, result.frame_index)
        if source_identity != self._displayed_source_identity:
            self.original_view.show_array(result.original_rgb)
            self._displayed_source_identity = source_identity
        self.mask_view.show_array(result.mask)
        self.result_view.show_array(result.segmented_rgb)
        self.source_label.configure(text=result.source.source_path.name)
        self.frame_var.set(
            "Frame: —" if result.frame_index is None else f"Frame: {result.frame_index}"
        )
        if result.histogram is not None:
            self.histogram_panel.set_histogram(result.histogram, result.thresholds)

    @property
    def histogram_visible(self) -> bool:
        return self._histogram_visible

    def toggle_histogram(self) -> None:
        self.set_histogram_visible(not self._histogram_visible)

    def set_histogram_visible(self, visible: bool) -> None:
        self._histogram_visible = bool(visible)
        if self._histogram_visible:
            self.histogram_panel.grid()
            self.histogram_toggle_button.configure(text="Hide Histogram")
        else:
            self.histogram_panel.grid_remove()
            self.histogram_toggle_button.configure(text="Show Histogram")

    def update_histogram_thresholds(self, thresholds, *, pending: bool = True) -> None:
        if pending:
            self.histogram_panel.mark_pending(thresholds)

    def mark_histogram_invalid(self) -> None:
        self.histogram_panel.mark_invalid()

    def show_status(self, message: str) -> None:
        self.status_var.set(message)

    def set_commands(
        self, *, open_image, open_video, save_mask, save_result, record_experiment,
        play, pause, restart
    ) -> None:
        self.open_image_button.configure(command=open_image)
        self.open_video_button.configure(command=open_video)
        self.save_mask_button.configure(command=save_mask)
        self.save_result_button.configure(command=save_result)
        self.experiment_panel.set_command(record_experiment)
        self.play_button.configure(command=play)
        self.pause_button.configure(command=pause)
        self.restart_button.configure(command=restart)

    def set_loading(self, loading: bool) -> None:
        state = "disabled" if loading else "normal"
        self.open_image_button.configure(state=state)
        self.open_video_button.configure(state=state)

    def set_export_available(self, available: bool) -> None:
        state = "normal" if available else "disabled"
        self.save_mask_button.configure(state=state)
        self.save_result_button.configure(state=state)

    def set_experiment_available(self, available: bool) -> None:
        self.experiment_panel.set_available(available)

    def update_video_controls(self, state: str) -> None:
        self.play_button.configure(state="normal" if state == "paused" else "disabled")
        self.pause_button.configure(state="normal" if state == "playing" else "disabled")
        self.restart_button.configure(
            state="normal" if state in {"paused", "playing", "ended", "error"} else "disabled"
        )
