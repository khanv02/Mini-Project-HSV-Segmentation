"""Top-level layout for the still-image MVP."""

import tkinter as tk
from tkinter import ttk

from ..models import SegmentationResult
from ..processing.visualization import compose_segmentation_overlay
from .experiment_panel import ExperimentPanel
from .hsv_histogram import HSVHistogramPanel
from .image_view import ImageView
from .theme import SPACING, configure_theme
from .tooltips import ToolTip


class MainWindow:
    """Compose named sections and three synchronized result views."""

    def __init__(self, root: tk.Tk | None = None):
        self.root = root or tk.Tk()
        self._displayed_source_identity: tuple[str, int | None] | None = None
        self._current_result: SegmentationResult | None = None
        self.media_context = "empty"
        self.root.title("HSV Color Segmentation")
        self.style = configure_theme(self.root)
        self.root.minsize(960, 640)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        initial_width = max(960, min(1400, screen_width - 80))
        initial_height = max(640, min(900, screen_height - 100))
        self.root.geometry(f"{initial_width}x{initial_height}")

        container = ttk.Frame(self.root, padding=10)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        self.input_section = ttk.LabelFrame(
            container, text="File Input", padding=SPACING["sm"]
        )
        self.input_section.grid(row=0, column=0, sticky="ew", pady=(0, SPACING["md"]))
        self.command_row = ttk.Frame(self.input_section, style="Surface.TFrame")
        self.command_row.pack(side="top", fill="x")
        self.open_image_button = ttk.Button(
            self.command_row, text="Open Image…", style="Primary.TButton"
        )
        self.open_image_button.pack(side="left")
        self.open_video_button = ttk.Button(self.command_row, text="Open Video…")
        self.open_video_button.pack(side="left", padx=(SPACING["sm"], 0))
        ttk.Separator(self.command_row, orient="vertical").pack(
            side="left", fill="y", padx=SPACING["md"]
        )
        self.save_mask_button = ttk.Button(
            self.command_row, text="Save Mask…", state="disabled"
        )
        self.save_mask_button.pack(side="left")
        self.save_result_button = ttk.Button(
            self.command_row, text="Save Result…", state="disabled"
        )
        self.save_result_button.pack(side="left", padx=(SPACING["sm"], 0))
        self.record_experiment_button = ttk.Button(
            self.command_row, text="Record Experiment…", state="disabled"
        )
        self.record_experiment_button.pack(side="left", padx=(SPACING["sm"], 0))

        self.context_row = ttk.Frame(self.input_section, style="Surface.TFrame")
        self.context_row.pack(side="bottom", fill="x", pady=(SPACING["sm"], 0))
        self.source_summary = ttk.Frame(self.context_row, style="Surface.TFrame")
        self.source_summary.pack(side="right")
        self.frame_var = tk.StringVar(value="Frame: —")
        self.frame_label = ttk.Label(
            self.source_summary, textvariable=self.frame_var, style="Muted.TLabel"
        )
        self.source_label = ttk.Label(
            self.source_summary, text="No image loaded", style="Surface.TLabel"
        )
        self.source_label.pack(side="right")

        self.video_controls = ttk.Frame(self.context_row, style="Surface.TFrame")
        self.play_button = ttk.Button(self.video_controls, text="Play", state="disabled")
        self.play_button.pack(side="left")
        self.pause_button = ttk.Button(self.video_controls, text="Pause", state="disabled")
        self.pause_button.pack(side="left", padx=(SPACING["xs"], 0))
        self.restart_button = ttk.Button(self.video_controls, text="Restart", state="disabled")
        self.restart_button.pack(side="left", padx=(SPACING["xs"], 0))

        self.workspace = ttk.Frame(container)
        self.workspace.grid(row=1, column=0, sticky="nsew")
        self.workspace.columnconfigure(0, minsize=300)
        self.workspace.columnconfigure(1, weight=1)
        self.workspace.rowconfigure(0, weight=1)

        self.parameter_section = ttk.LabelFrame(
            self.workspace, text="HSV Parameters", padding=SPACING["sm"]
        )
        self.parameter_section.grid(
            row=0, column=0, sticky="nsew", padx=(0, SPACING["md"])
        )

        self.experiment_panel = ExperimentPanel(self.root)

        self.visualization_section = ttk.LabelFrame(
            self.workspace, text="Result Visualization", padding=SPACING["sm"]
        )
        self.visualization_section.grid(row=0, column=1, sticky="nsew")
        for column in range(3):
            self.visualization_section.columnconfigure(column, weight=1, uniform="view")
        self.visualization_section.rowconfigure(2, weight=1)

        visualization_toolbar = ttk.Frame(self.visualization_section)
        visualization_toolbar.grid(
            row=0, column=0, columnspan=3, sticky="ew", padx=SPACING["xs"]
        )
        self.pick_color_button = ttk.Button(
            visualization_toolbar, text="Pick Color", state="disabled"
        )
        self.pick_color_button.pack(side="left")
        self.sampling_mode_var = tk.StringVar(value="Pixel")
        self.sampling_mode_box = ttk.Combobox(
            visualization_toolbar,
            textvariable=self.sampling_mode_var,
            values=("Pixel", "ROI"),
            state="disabled",
            width=6,
        )
        self.sampling_mode_box.pack(side="left", padx=(5, 0))
        self.sampling_mode_box.bind(
            "<<ComboboxSelected>>", lambda _event: self._apply_sampling_mode()
        )
        self.sample_var = tk.StringVar(value="Sample: —")
        ttk.Label(visualization_toolbar, textvariable=self.sample_var).pack(
            side="left", padx=(8, 0)
        )
        self.histogram_toggle_button = ttk.Button(
            visualization_toolbar, text="Show Histogram", command=self.toggle_histogram
        )
        self.histogram_toggle_button.pack(side="right")
        visualization_info = ttk.Frame(self.visualization_section)
        visualization_info.grid(
            row=1, column=0, columnspan=3, sticky="ew", padx=SPACING["xs"],
            pady=(SPACING["xs"], SPACING["xs"]),
        )
        self.overlay_var = tk.BooleanVar(value=False)
        self.overlay_button = ttk.Checkbutton(
            visualization_info,
            text="Overlay mode",
            variable=self.overlay_var,
            command=self._refresh_result_view,
        )
        self.overlay_button.pack(side="right", padx=(0, 10))
        self.original_mask_var = tk.BooleanVar(value=False)
        self.original_mask_button = ttk.Checkbutton(
            visualization_info,
            text="Compare HSV mask",
            variable=self.original_mask_var,
            command=self._refresh_mask_view,
            state="disabled",
        )
        self.original_mask_button.pack(side="right", padx=(0, 10))
        self.selection_var = tk.StringVar(value="Selected pixels: —")
        ttk.Label(visualization_info, textvariable=self.selection_var).pack(
            side="left"
        )
        self._tooltips = (
            ToolTip(
                self.pick_color_button,
                "Sample a pixel from the Original view and suggest HSV thresholds around it.",
            ),
            ToolTip(
                self.sampling_mode_box,
                "Pixel samples one point; ROI lets you drag a representative rectangular region.",
            ),
            ToolTip(
                self.histogram_toggle_button,
                "Show or hide source HSV distributions and the active threshold ranges.",
            ),
            ToolTip(
                self.overlay_button,
                "Tint selected pixels over the original image; saved results remain unchanged.",
            ),
            ToolTip(
                self.original_mask_button,
                "Switch the Binary Mask panel between the original HSV mask and morphology result. Saving uses the processed result.",
            ),
        )

        self.original_view = ImageView(self.visualization_section, title="Original")
        self.mask_view = ImageView(
            self.visualization_section, title="Binary Mask", is_mask=True
        )
        self.result_view = ImageView(self.visualization_section, title="Segmented Result")
        self.views = (self.original_view, self.mask_view, self.result_view)
        for column, view in enumerate(self.views):
            view.grid(row=2, column=column, sticky="nsew", padx=SPACING["xs"])

        self.histogram_panel = HSVHistogramPanel(self.visualization_section)
        self.histogram_panel.grid(
            row=3, column=0, columnspan=3, sticky="ew", padx=SPACING["xs"],
            pady=(SPACING["xs"], 0)
        )
        self.histogram_panel.grid_remove()
        self._histogram_visible = False

        self.status_var = tk.StringVar(value="Ready — open a PNG, JPEG, or BMP image.")
        self.status_label = ttk.Label(
            container, textvariable=self.status_var, anchor="w", style="Status.TLabel"
        )
        self.status_label.grid(
            row=2, column=0, sticky="ew", pady=(SPACING["sm"], 0)
        )
        self.root.bind("<Control-o>", lambda _event: self.open_image_button.invoke(), add="+")
        self.root.bind(
            "<Control-Shift-O>", lambda _event: self.open_video_button.invoke(), add="+"
        )

    def show_result(self, result: SegmentationResult) -> None:
        self._current_result = result
        self.set_media_context(result.source.media_kind)
        source_identity = (result.session_id, result.frame_index)
        if source_identity != self._displayed_source_identity:
            self.original_view.show_array(result.original_rgb)
            self._displayed_source_identity = source_identity
        if result.morphology.enabled:
            self.original_mask_button.configure(state="normal")
        else:
            self.original_mask_var.set(False)
            self.original_mask_button.configure(state="disabled")
        self._refresh_mask_view()
        self._refresh_result_view()
        self.source_label.configure(text=result.source.source_path.name)
        self.frame_var.set(
            "Frame: —" if result.frame_index is None else f"Frame: {result.frame_index}"
        )
        if result.histogram is not None:
            self.histogram_panel.set_histogram(result.histogram, result.thresholds)
        self.selection_var.set(
            f"Selected pixels: {result.selected_pixel_percentage:.2f}% "
            f"({result.selected_pixel_count:,}/{result.mask.size:,})"
        )

    @property
    def overlay_visible(self) -> bool:
        return bool(self.overlay_var.get())

    def _refresh_result_view(self) -> None:
        if self._current_result is None:
            return
        if self.overlay_visible:
            self.result_view.configure(text="Segmentation Overlay")
            self.result_view.show_array(compose_segmentation_overlay(
                self._current_result.original_rgb, self._current_result.mask
            ))
        else:
            self.result_view.configure(text="Segmented Result")
            self.result_view.show_array(self._current_result.segmented_rgb)

    def _refresh_mask_view(self) -> None:
        if self._current_result is None:
            return
        show_original = (
            self._current_result.morphology.enabled and self.original_mask_var.get()
        )
        if show_original:
            self.mask_view.configure(text="Original HSV Mask")
            self.mask_view.show_array(self._current_result.original_mask)
        else:
            title = (
                "Post-processed Mask"
                if self._current_result.morphology.enabled
                else "Binary Mask"
            )
            self.mask_view.configure(text=title)
            self.mask_view.show_array(self._current_result.mask)

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

    def mark_selection_pending(self) -> None:
        if self._displayed_source_identity is not None:
            self.selection_var.set("Selected pixels: processing…")

    def show_color_sample(self, sample) -> None:
        self.sample_var.set(
            f"Sample ({sample.x}, {sample.y}): "
            f"H {sample.hue_deg:.1f}°, S {sample.saturation_pct:.1f}%, "
            f"V {sample.value_pct:.1f}%"
        )

    def show_region_sample(self, sample) -> None:
        self.sample_var.set(
            f"ROI {sample.right - sample.left}×{sample.bottom - sample.top}: "
            f"H {sample.hue_deg:.1f}°, S {sample.saturation_pct:.1f}%, "
            f"V {sample.value_pct:.1f}%"
        )

    def show_status(self, message: str) -> None:
        self.status_var.set(message)

    def set_commands(
        self, *, open_image, open_video, save_mask, save_result, record_experiment,
        play, pause, restart, pick_color
    ) -> None:
        self.open_image_button.configure(command=open_image)
        self.open_video_button.configure(command=open_video)
        self.save_mask_button.configure(command=save_mask)
        self.save_result_button.configure(command=save_result)
        self.play_button.configure(command=play)
        self.pause_button.configure(command=pause)
        self.restart_button.configure(command=restart)
        self.pick_color_button.configure(command=pick_color)
        self.record_experiment_button.configure(command=self.experiment_panel.show)
        self.experiment_panel.set_command(record_experiment)

    def set_sampling_available(self, available: bool) -> None:
        self.pick_color_button.configure(state="normal" if available else "disabled")
        self.sampling_mode_box.configure(state="readonly" if available else "disabled")

    def set_color_picker_active(self, active: bool) -> None:
        self._apply_sampling_mode()
        self.original_view.set_sampling_enabled(active)
        self.pick_color_button.configure(text="Cancel Picking" if active else "Pick Color")

    def _apply_sampling_mode(self) -> None:
        self.original_view.set_sampling_mode(self.sampling_mode_var.get().lower())

    def set_loading(self, loading: bool) -> None:
        state = "disabled" if loading else "normal"
        self.open_image_button.configure(state=state)
        self.open_video_button.configure(state=state)

    def set_export_available(self, available: bool) -> None:
        state = "normal" if available else "disabled"
        self.save_mask_button.configure(state=state)
        self.save_result_button.configure(state=state)

    def set_experiment_available(self, available: bool) -> None:
        self.record_experiment_button.configure(
            state="normal" if available else "disabled"
        )
        self.experiment_panel.set_available(available)

    def update_video_controls(self, state: str) -> None:
        if state in {"paused", "playing", "ended", "error"}:
            self.set_media_context("video")
        elif self._current_result is not None:
            self.set_media_context(self._current_result.source.media_kind)
        else:
            self.set_media_context("empty")
        self.play_button.configure(state="normal" if state == "paused" else "disabled")
        self.pause_button.configure(state="normal" if state == "playing" else "disabled")
        self.restart_button.configure(
            state="normal" if state in {"paused", "playing", "ended", "error"} else "disabled"
        )

    def set_media_context(self, context: str) -> None:
        """Reveal media-specific commands without changing application state."""
        if context not in {"empty", "image", "video"}:
            raise ValueError("media context must be empty, image, or video")
        self.media_context = context
        if context == "video":
            if not self.video_controls.winfo_manager():
                self.video_controls.pack(
                    side="left", padx=(SPACING["md"], 0), before=self.source_summary
                )
            if not self.frame_label.winfo_manager():
                self.frame_label.pack(side="right", padx=(SPACING["sm"], 0))
            return

        focus = self.root.focus_get()
        if focus is not None and str(focus).startswith(str(self.video_controls)):
            self.open_image_button.focus_set()
        self.video_controls.pack_forget()
        self.frame_label.pack_forget()
        self.frame_var.set("Frame: —")
