"""Top-level layout for the still-image MVP."""

import tkinter as tk
from tkinter import ttk

from ..models import SegmentationResult
from ..processing.visualization import (
    compose_confusion_overlay, compose_region_annotations, compose_segmentation_overlay,
    compose_watershed_overlay,
)
from .experiment_panel import ExperimentPanel
from .hsv_histogram import HSVHistogramPanel
from .image_view import ImageView
from .theme import SPACING, configure_theme
from .tooltips import ToolTip


class MainWindow:
    """Compose compact controls and four synchronized result views."""

    def __init__(self, root: tk.Tk | None = None):
        self.root = root or tk.Tk()
        self._displayed_source_identity: tuple[str, int | None] | None = None
        self._current_result: SegmentationResult | None = None
        self._analysis_display = (True, True, False)
        self.media_context = "empty"
        self.root.title("HSV Color Segmentation")
        self.style = configure_theme(self.root)
        self.root.minsize(1100, 720)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        initial_width = max(1100, min(1440, screen_width - 80))
        initial_height = max(720, min(900, screen_height - 100))
        self.root.geometry(f"{initial_width}x{initial_height}")

        container = ttk.Frame(self.root, padding=SPACING["sm"], style="App.TFrame")
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        self.input_section = ttk.Frame(
            container, padding=SPACING["sm"], style="Card.TFrame"
        )
        self.input_section.grid(row=0, column=0, sticky="ew", pady=(0, SPACING["sm"]))
        self.command_row = ttk.Frame(self.input_section, style="Toolbar.TFrame")
        self.command_row.pack(side="top", fill="x")
        self.open_image_button = ttk.Button(
            self.command_row, text="Open Image…", style="Primary.TButton"
        )
        self.open_image_button.pack(side="left")
        self.open_video_button = ttk.Button(self.command_row, text="Open Video…")
        self.open_video_button.pack(side="left", padx=(SPACING["sm"], 0))
        self.output_actions = ttk.Frame(self.command_row, style="Toolbar.TFrame")
        self.output_actions.pack(side="right")
        self.save_mask_button = ttk.Button(
            self.output_actions, text="Save Mask…", state="disabled"
        )
        self.save_mask_button.pack(side="left")
        self.save_result_button = ttk.Button(
            self.output_actions, text="Save Result…", state="disabled"
        )
        self.save_result_button.pack(side="left", padx=(SPACING["xs"], 0))
        self.record_experiment_button = ttk.Button(
            self.output_actions, text="Record Experiment…", state="disabled"
        )
        self.record_experiment_button.pack(side="left", padx=(SPACING["xs"], 0))

        self.source_summary = ttk.Frame(self.command_row, style="Toolbar.TFrame")
        self.source_summary.pack(side="right", padx=(SPACING["sm"], 0))
        self.frame_var = tk.StringVar(value="Frame: —")
        self.frame_label = ttk.Label(
            self.source_summary, textvariable=self.frame_var, style="Muted.TLabel"
        )
        self.source_label = ttk.Label(
            self.source_summary, text="No image loaded", style="Surface.TLabel"
        )
        self.source_label.pack(side="right")

        self.video_controls = ttk.Frame(self.command_row, style="Toolbar.TFrame")
        self.play_button = ttk.Button(self.video_controls, text="Play", state="disabled")
        self.play_button.pack(side="left")
        self.pause_button = ttk.Button(self.video_controls, text="Pause", state="disabled")
        self.pause_button.pack(side="left", padx=(SPACING["xs"], 0))
        self.restart_button = ttk.Button(self.video_controls, text="Restart", state="disabled")
        self.restart_button.pack(side="left", padx=(SPACING["xs"], 0))

        self.workspace = ttk.Frame(container, style="App.TFrame")
        self.workspace.grid(row=1, column=0, sticky="nsew")
        self.workspace.columnconfigure(0, weight=1)
        self.workspace.rowconfigure(1, weight=1)

        self.parameter_section = ttk.Frame(
            self.workspace, padding=(SPACING["sm"], 4), style="Card.TFrame"
        )
        self.parameter_section.grid(row=0, column=0, sticky="ew")
        self.control_notebook = ttk.Notebook(self.parameter_section)
        self.control_notebook.pack(fill="x")

        self.hsv_controls_tab = ttk.Frame(
            self.control_notebook, padding=SPACING["sm"]
        )
        self.refine_controls_tab = ttk.Frame(
            self.control_notebook, padding=SPACING["sm"]
        )
        self.analysis_controls_tab = ttk.Frame(
            self.control_notebook, padding=SPACING["sm"]
        )
        self.control_notebook.add(self.hsv_controls_tab, text="  HSV Thresholds  ")
        self.control_notebook.add(self.refine_controls_tab, text="  Refine Mask  ")
        self.control_notebook.add(self.analysis_controls_tab, text="  Analyze  ")
        self.control_sections = {
            "hsv": self.hsv_controls_tab,
            "refine": self.refine_controls_tab,
            "analyze": self.analysis_controls_tab,
        }

        self.experiment_panel = ExperimentPanel(self.root)

        self.visualization_section = ttk.Frame(
            self.workspace, padding=SPACING["sm"], style="Card.TFrame"
        )
        self.visualization_section.grid(
            row=1, column=0, sticky="nsew", pady=(SPACING["sm"], 0)
        )
        for column in range(4):
            self.visualization_section.columnconfigure(column, weight=1, uniform="view")
        self.visualization_section.rowconfigure(2, weight=1)

        visualization_toolbar = ttk.Frame(self.visualization_section)
        visualization_toolbar.grid(
            row=0, column=0, columnspan=4, sticky="ew", padx=SPACING["xs"]
        )
        ttk.Label(
            visualization_toolbar, text="Preview", style="Title.TLabel"
        ).pack(side="left", padx=(0, SPACING["md"]))
        self.pick_color_button = ttk.Button(
            visualization_toolbar, text="Pick Color", state="disabled"
        )
        self.pick_color_button.pack(side="left")
        self.sampling_mode_var = tk.StringVar(value="Pixel")
        self.sampling_mode_box = ttk.Combobox(
            visualization_toolbar,
            textvariable=self.sampling_mode_var,
            values=("Pixel", "Multi", "ROI"),
            state="disabled",
            width=7,
        )
        self.sampling_mode_box.pack(side="left", padx=(5, 0))
        self.sampling_mode_box.bind(
            "<<ComboboxSelected>>", lambda _event: self._apply_sampling_mode()
        )
        self.clear_samples_button = ttk.Button(
            visualization_toolbar, text="Clear Points", state="disabled"
        )
        self.clear_samples_button.pack(side="left", padx=(5, 0))
        self.sample_var = tk.StringVar(value="Sample: —")
        ttk.Label(visualization_toolbar, textvariable=self.sample_var).pack(
            side="left", padx=(8, 0)
        )
        self.histogram_toggle_button = ttk.Button(
            visualization_toolbar, text="Hide Histogram", command=self.toggle_histogram
        )
        self.histogram_toggle_button.pack(side="right")
        visualization_info = ttk.Frame(self.visualization_section)
        visualization_info.grid(
            row=1, column=0, columnspan=4, sticky="ew", padx=SPACING["xs"],
            pady=(SPACING["xs"], SPACING["xs"]),
        )
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
                "Pixel samples one point; Multi combines 2–4 clicked points; ROI samples a rectangle.",
            ),
            ToolTip(
                self.clear_samples_button,
                "Remove all points collected by the current Multi sampling session.",
            ),
            ToolTip(
                self.histogram_toggle_button,
                "Show or hide source HSV distributions and the active threshold ranges.",
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
        self.overlay_view = ImageView(self.visualization_section, title="Overlay")
        self.views = (
            self.original_view,
            self.mask_view,
            self.result_view,
            self.overlay_view,
        )
        for column, view in enumerate(self.views):
            view.grid(row=2, column=column, sticky="nsew", padx=SPACING["xs"])

        self.histogram_panel = HSVHistogramPanel(self.visualization_section)
        self.histogram_panel.grid(
            row=3, column=0, columnspan=4, sticky="ew", padx=SPACING["xs"],
            pady=(SPACING["xs"], 0)
        )
        self._histogram_visible = True

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

    def _refresh_result_view(self) -> None:
        if self._current_result is None:
            return
        self.result_view.configure(text="Segmented Result")
        self.result_view.show_array(self._current_result.segmented_rgb)
        contours, boxes, confusion = self._analysis_display
        if confusion and self._current_result.evaluation is not None and self._current_result.ground_truth is not None:
            target = self._evaluation_mask(self._current_result)
            self.overlay_view.configure(text="Overlay · TP / FP / FN")
            self.overlay_view.show_array(compose_confusion_overlay(
                self._current_result.original_rgb, target, self._current_result.ground_truth.mask
            ))
        elif (
            self._current_result.watershed is not None
            and self._current_result.watershed.status == "applied"
        ):
            self.overlay_view.configure(text="Overlay · Watershed")
            separated = compose_watershed_overlay(
                self._current_result.original_rgb, self._current_result.watershed
            )
            if self._current_result.watershed.analysis is not None and (contours or boxes):
                separated = compose_region_annotations(
                    separated, self._current_result.watershed.analysis,
                    contours=contours, boxes=boxes,
                )
            self.overlay_view.show_array(separated)
        elif self._current_result.analysis is not None and (contours or boxes):
            self.overlay_view.configure(text="Overlay · Object Analysis")
            self.overlay_view.show_array(compose_region_annotations(
                self._current_result.original_rgb, self._current_result.analysis,
                contours=contours, boxes=boxes,
            ))
        else:
            self.overlay_view.configure(text="Overlay")
            self.overlay_view.show_array(compose_segmentation_overlay(
                self._current_result.original_rgb, self._current_result.mask
            ))

    @staticmethod
    def _evaluation_mask(result: SegmentationResult):
        if result.evaluation_target == "components" and result.analysis is not None:
            return result.analysis.filtered_mask
        if result.evaluation_target == "watershed" and result.watershed is not None:
            return result.watershed.foreground_mask
        return result.mask

    def set_analysis_display(self, contours: bool, boxes: bool, confusion: bool) -> None:
        self._analysis_display = (bool(contours), bool(boxes), bool(confusion))
        self._refresh_result_view()

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

    def show_multi_sample(self, sample, *, active: bool) -> None:
        self.sample_var.set(
            f"Multi {sample.pixel_count}/4: H {sample.hue_deg:.1f}°, "
            f"S {sample.saturation_pct:.1f}%, V {sample.value_pct:.1f}%"
        )
        self.clear_samples_button.configure(state="normal")
        if active:
            self.pick_color_button.configure(text=f"Finish Multi ({sample.pixel_count}/4)")

    def show_multi_sample_waiting(self) -> None:
        self.sample_var.set("Multi 1/4: choose at least one more point")
        self.clear_samples_button.configure(state="normal")
        self.pick_color_button.configure(text="Finish Multi (1/4)")

    def clear_sample_summary(self) -> None:
        self.sample_var.set("Sample: —")
        self.clear_samples_button.configure(state="disabled")

    def show_status(self, message: str) -> None:
        self.status_var.set(message)

    def set_commands(
        self, *, open_image, open_video, save_mask, save_result, record_experiment,
        play, pause, restart, pick_color, clear_samples, sampling_mode_changed
    ) -> None:
        self.open_image_button.configure(command=open_image)
        self.open_video_button.configure(command=open_video)
        self.save_mask_button.configure(command=save_mask)
        self.save_result_button.configure(command=save_result)
        self.play_button.configure(command=play)
        self.pause_button.configure(command=pause)
        self.restart_button.configure(command=restart)
        self.pick_color_button.configure(command=pick_color)
        self.clear_samples_button.configure(command=clear_samples)
        self._sampling_mode_changed = sampling_mode_changed
        self.record_experiment_button.configure(command=self.experiment_panel.show)
        self.experiment_panel.set_command(record_experiment)

    def set_sampling_available(self, available: bool) -> None:
        self.pick_color_button.configure(state="normal" if available else "disabled")
        self.sampling_mode_box.configure(state="readonly" if available else "disabled")
        if not available:
            self.clear_samples_button.configure(state="disabled")

    def set_color_picker_active(self, active: bool) -> None:
        self.original_view.set_sampling_mode(self.sampling_mode_var.get().lower())
        self.original_view.set_sampling_enabled(active)
        self.pick_color_button.configure(text="Cancel Picking" if active else "Pick Color")

    def _apply_sampling_mode(self) -> None:
        self.original_view.set_sampling_mode(self.sampling_mode_var.get().lower())
        callback = getattr(self, "_sampling_mode_changed", None)
        if callback is not None:
            callback(self.sampling_mode_var.get().lower())

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

        try:
            focus = self.root.focus_get()
        except (KeyError, tk.TclError):
            # ttk combobox popdown windows can disappear between Tcl lookup and
            # Tkinter's widget-name resolution during rapid background updates.
            focus = None
        if focus is not None and str(focus).startswith(str(self.video_controls)):
            self.open_image_button.focus_set()
        self.video_controls.pack_forget()
        self.frame_label.pack_forget()
        self.frame_var.set("Frame: —")
