"""Main-thread controller for still-image and sequential-video workflows."""

from collections.abc import Callable
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from ..application.playback import (
    PlaybackAdvance,
    PlaybackSession,
    PlaybackState,
    VideoCandidate,
)
from ..application.processing_worker import ProcessingWorker, WorkerCompletion
from ..application.session import ImageSession
from ..errors import ValidationError, format_recovery_message
from ..io.export import ExportReceipt, export_snapshot
from ..io.experiments import ExperimentReceipt, publish_experiment
from ..models import (
    HSVThresholdSet,
    MorphologySettings,
    ProcessingRequest,
    SegmentationResult,
)
from ..processing.threshold_suggestions import (
    sample_color,
    sample_color_region,
    suggest_thresholds,
)
from .main_window import MainWindow
from .morphology_controls import MorphologyControls
from .threshold_controls import ThresholdControls


class ApplicationController:
    """Connect dialogs/widgets to serialized application and I/O services."""

    POLL_MS = 25

    def __init__(
        self,
        root: tk.Tk,
        *,
        exporter: Callable[..., ExportReceipt] = export_snapshot,
        experiment_recorder: Callable[..., ExperimentReceipt] = publish_experiment,
    ):
        self.root = root
        self.window = MainWindow(root)
        self.session = ImageSession()
        self.playback = PlaybackSession(self.session)
        self.worker = ProcessingWorker()
        self._exporter = exporter
        self._experiment_recorder = experiment_recorder
        self.experiment_panel = self.window.experiment_panel
        self.controls = ThresholdControls(
            self.window.parameter_section,
            initial=self.session.thresholds,
            on_valid=self._on_thresholds,
            on_invalid=self._on_invalid_thresholds,
        )
        self.morphology_controls = MorphologyControls(
            self.window.parameter_section,
            initial=self.session.morphology,
            on_change=self._on_morphology,
        )
        self.window.original_view.set_sample_callback(self._on_color_sample)
        self.window.original_view.set_roi_sample_callback(self._on_roi_sample)
        self._latest_request_revision = 0
        self._video_request_in_flight: int | None = None
        self._resume_video_on_failure = False
        self._resume_video_after_export = False
        self._export_in_flight = False
        self._export_snapshot_valid = False
        self._color_picker_active = False
        self.last_export_receipt: ExportReceipt | None = None
        self.last_experiment_receipt: ExperimentReceipt | None = None
        self._closed = False
        self.window.set_commands(
            open_image=self.choose_image,
            open_video=self.choose_video,
            save_mask=self.choose_save_mask,
            save_result=self.choose_save_result,
            record_experiment=self.choose_record_experiment,
            play=self.play_video,
            pause=self.pause_video,
            restart=self.restart_video,
            pick_color=self.toggle_color_picker,
        )
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._poll_id = self.root.after(self.POLL_MS, self._poll_worker)

    def choose_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[
                ("Supported images", "*.png *.jpg *.jpeg *.bmp"),
                ("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("BMP", "*.bmp"),
            ],
        )
        if path:
            self.open_image_path(path)

    def open_image_path(self, path: str) -> None:
        self._pause_for_candidate_open()
        self._set_color_picker_active(False)
        self.window.set_sampling_available(False)
        revision = self._next_revision(invalidate_video=True)
        self.window.set_loading(True)
        self.controls.set_enabled(False)
        self._export_snapshot_valid = False
        self._refresh_export_controls()
        self.window.show_status("Loading and processing image…")
        self.morphology_controls.set_enabled(False)
        self.worker.submit_image(
            path, self.session.thresholds, revision, self.session.morphology
        )

    def choose_video(self) -> None:
        path = filedialog.askopenfilename(
            title="Open Video",
            filetypes=[
                ("Supported videos", "*.mp4 *.avi"),
                ("MP4", "*.mp4"), ("AVI", "*.avi"),
            ],
        )
        if path:
            self.open_video_path(path)

    def open_video_path(self, path: str) -> None:
        self._pause_for_candidate_open()
        self._set_color_picker_active(False)
        self.window.set_sampling_available(False)
        revision = self._next_revision(invalidate_video=True)
        thresholds = self.session.thresholds
        morphology = self.session.morphology
        self.window.set_loading(True)
        self.controls.set_enabled(False)
        self.morphology_controls.set_enabled(False)
        self._export_snapshot_valid = False
        self._refresh_export_controls()
        self.window.show_status("Opening video and decoding its first frame…")
        self.worker.submit_operation(
            "video_open", revision,
            lambda: self.playback.prepare_open(
                path, thresholds, revision, morphology
            ),
            cleanup=lambda candidate: candidate.reader.release(),
        )

    def _pause_for_candidate_open(self) -> None:
        self._resume_video_on_failure = self.playback.state is PlaybackState.PLAYING
        if self._resume_video_on_failure:
            self.playback.pause()

    def _next_revision(self, *, invalidate_video: bool = False) -> int:
        self._latest_request_revision += 1
        if invalidate_video:
            self._video_request_in_flight = None
        return self._latest_request_revision

    def play_video(self) -> None:
        self._set_color_picker_active(False)
        if self.playback.play():
            self.window.update_video_controls(self.playback.state.value)
            self.window.show_status(self.playback.status_message)
            self._schedule_video_frame()

    def pause_video(self) -> None:
        if self.playback.pause():
            self.window.update_video_controls(self.playback.state.value)
            self.window.show_status(self.playback.status_message)

    def restart_video(self) -> None:
        if not self.playback.has_video:
            return
        self._set_color_picker_active(False)
        self.playback.pause()
        revision = self._next_revision(invalidate_video=True)
        thresholds = self.session.thresholds
        morphology = self.session.morphology
        self._export_snapshot_valid = False
        self._refresh_export_controls()
        self.window.show_status("Restarting video…")
        self.worker.submit_operation(
            "video_restart", revision,
            lambda: self.playback.prepare_restart(thresholds, revision, morphology),
        )

    def _schedule_video_frame(self) -> None:
        if (
            self._closed
            or self.playback.state is not PlaybackState.PLAYING
            or self._video_request_in_flight is not None
        ):
            return
        revision = self._next_revision()
        self._video_request_in_flight = revision
        thresholds = self.session.thresholds
        morphology = self.session.morphology
        self.worker.submit_operation(
            "video_frame", revision,
            lambda: self.playback.prepare_next(thresholds, revision, morphology),
        )

    def _on_thresholds(self, thresholds: HSVThresholdSet) -> None:
        self.session.accept_thresholds(thresholds)
        source = self.session.source
        self.window.update_histogram_thresholds(
            thresholds, pending=source is not None
        )
        if source is None:
            self.window.show_status("Thresholds ready — open an image or video.")
            return
        revision = self._next_revision(invalidate_video=True)
        request = ProcessingRequest(
            source, thresholds, revision, self.session.morphology
        )
        self._export_snapshot_valid = False
        self._refresh_export_controls()
        self.window.show_status("Parameters changed — result pending…")
        self.window.mark_selection_pending()
        self.worker.submit(request)

    def _on_morphology(self, morphology: MorphologySettings) -> None:
        self.session.accept_morphology(morphology)
        source = self.session.source
        if source is None:
            state = "enabled" if morphology.enabled else "disabled"
            self.window.show_status(
                f"Morphology {state} — open an image or video."
            )
            return
        revision = self._next_revision(invalidate_video=True)
        request = ProcessingRequest(
            source, self.session.thresholds, revision, morphology
        )
        self._export_snapshot_valid = False
        self._refresh_export_controls()
        self.window.mark_selection_pending()
        self.window.show_status("Morphology changed — result pending…")
        self.worker.submit(request)

    def toggle_color_picker(self) -> None:
        if self.window.original_view.source_array is None:
            self.window.show_status("Open an image or video before using the color picker.")
            return
        if not self._color_picker_active and self.playback.state is PlaybackState.PLAYING:
            self.pause_video()
        self._set_color_picker_active(not self._color_picker_active)
        if self._color_picker_active:
            self.window.show_status("Color picker active — click a pixel in the Original view.")
        else:
            self.window.show_status("Color picker cancelled.")

    def _set_color_picker_active(self, active: bool) -> None:
        self._color_picker_active = bool(active)
        self.window.set_color_picker_active(self._color_picker_active)

    def _on_color_sample(self, x: int, y: int) -> None:
        displayed_rgb = self.window.original_view.source_array
        if not self._color_picker_active or displayed_rgb is None:
            return
        sample = sample_color(displayed_rgb, x, y)
        suggestion = suggest_thresholds(sample)
        self._set_color_picker_active(False)
        self.window.show_color_sample(sample)
        self.controls.apply_thresholds(suggestion)
        self.window.show_status(
            f"Sampled RGB {sample.rgb} at ({x}, {y}); suggested HSV thresholds applied."
        )

    def _on_roi_sample(self, left: int, top: int, right: int, bottom: int) -> None:
        displayed_rgb = self.window.original_view.source_array
        if not self._color_picker_active or displayed_rgb is None:
            return
        sample = sample_color_region(displayed_rgb, left, top, right, bottom)
        self._set_color_picker_active(False)
        self.window.show_region_sample(sample)
        self.controls.apply_thresholds(sample.thresholds)
        self.window.show_status(
            f"Sampled {sample.pixel_count:,} pixels from ROI "
            f"({left}, {top})–({right}, {bottom}); suggested HSV thresholds applied."
        )

    def _on_invalid_thresholds(self, error: ValidationError) -> None:
        self._export_snapshot_valid = False
        self.window.mark_histogram_invalid()
        self._refresh_export_controls()
        self.window.show_status(
            format_recovery_message(
                error,
                operation="validate HSV thresholds",
                affected=error.field,
                preserved_state=(
                    "The previous valid thresholds and result were preserved; saving is disabled "
                    "until all visible values are valid."
                ),
            )
        )

    @property
    def export_in_flight(self) -> bool:
        return self._export_in_flight

    def choose_save_mask(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save Binary Mask",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
            confirmoverwrite=False,
        )
        self.save_mask_path(path or None)

    def choose_save_result(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save Segmented Result",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
            confirmoverwrite=False,
        )
        self.save_result_path(path or None)

    def save_mask_path(self, path: str | Path | None) -> bool:
        return self._begin_export("mask", path)

    def save_result_path(self, path: str | Path | None) -> bool:
        return self._begin_export("result", path)

    def choose_record_experiment(self) -> None:
        runs_dir = filedialog.askdirectory(title="Choose Experiment Runs Directory")
        if runs_dir:
            started = self.record_experiment_to(
                runs_dir, Path.cwd() / "experiments" / "environment.json"
            )
            if started:
                self.experiment_panel.hide()

    def record_experiment_to(
        self,
        runs_dir: str | Path | None,
        environment_path: str | Path | None = None,
    ) -> bool:
        if runs_dir is None or str(runs_dir) == "":
            return False
        snapshot = self.session.result
        lighting, observations = self.experiment_panel.descriptions()
        if not lighting or not observations:
            self.window.show_status(
                "Lighting and observations are required before recording an experiment."
            )
            return False
        if (
            self._export_in_flight
            or not self._export_snapshot_valid
            or snapshot is None
            or snapshot.thresholds != self.session.thresholds
            or snapshot.morphology != self.session.morphology
        ):
            self.window.show_status(
                "Recording is unavailable until a complete current result is ready."
            )
            return False
        environment = Path(environment_path or Path.cwd() / "experiments" / "environment.json")
        self._resume_video_after_export = self.playback.state is PlaybackState.PLAYING
        if self._resume_video_after_export:
            self.playback.pause()
            self.window.update_video_controls(self.playback.state.value)
        revision = self._latest_request_revision
        self._export_in_flight = True
        self._refresh_export_controls()
        self.window.show_status("Recording experiment…")
        self.worker.submit_operation(
            "experiment_record",
            revision,
            lambda: self._experiment_recorder(
                snapshot, lighting, observations, Path(runs_dir), environment
            ),
            replace_pending=False,
        )
        return True

    def _begin_export(self, kind: str, path: str | Path | None) -> bool:
        if path is None or str(path) == "":
            return False
        snapshot = self.session.result
        if (
            self._export_in_flight
            or not self._export_snapshot_valid
            or snapshot is None
            or snapshot.thresholds != self.session.thresholds
            or snapshot.morphology != self.session.morphology
        ):
            self.window.show_status(
                "Saving is unavailable until a complete current result is ready."
            )
            return False
        target = Path(path).resolve()
        overwrite = target.exists()
        if overwrite and not messagebox.askyesno(
            "Confirm Overwrite",
            f"Replace the existing file?\n{target}",
            parent=self.root,
        ):
            return False
        self._resume_video_after_export = self.playback.state is PlaybackState.PLAYING
        if self._resume_video_after_export:
            self.playback.pause()
            self.window.update_video_controls(self.playback.state.value)
        revision = self._latest_request_revision
        self._export_in_flight = True
        self._refresh_export_controls()
        label = "mask" if kind == "mask" else "segmented result"
        self.window.show_status(f"Saving {label}…")
        self.worker.submit_operation(
            f"export_{kind}",
            revision,
            lambda: self._exporter(snapshot, kind, target, overwrite=overwrite),
            replace_pending=False,
        )
        return True

    def _refresh_export_controls(self) -> None:
        result = self.session.result
        available = (
            not self._closed
            and not self._export_in_flight
            and self._export_snapshot_valid
            and result is not None
            and result.thresholds == self.session.thresholds
            and result.morphology == self.session.morphology
        )
        self.window.set_export_available(available)
        self.window.set_experiment_available(available)

    def _poll_worker(self) -> None:
        if self._closed:
            return
        for completion in self.worker.poll():
            self._handle_completion(completion)
        self._poll_id = self.root.after(self.POLL_MS, self._poll_worker)

    def _handle_completion(self, completion: WorkerCompletion) -> None:
        if completion.kind in {"export_mask", "export_result", "experiment_record"}:
            self._handle_export_completion(completion)
            return
        if completion.request_revision == self._video_request_in_flight:
            self._video_request_in_flight = None
        if completion.request_revision != self._latest_request_revision:
            if completion.kind == "video_open" and isinstance(
                completion.result, VideoCandidate
            ):
                completion.result.reader.release()
            return
        if completion.error is not None:
            self._handle_error(completion)
            return
        result = self._accept_completion(completion)
        if result is None:
            return
        self._resume_video_on_failure = False
        self._export_snapshot_valid = True
        self.window.show_result(result)
        self.window.set_loading(False)
        self.controls.set_enabled(True)
        self.morphology_controls.set_enabled(True)
        self.window.set_sampling_available(True)
        self.window.update_video_controls(self.playback.state.value)
        self._refresh_export_controls()
        morphology_status = "Morphology off"
        if result.morphology.enabled:
            operation = result.morphology.operation.replace("_", " + ").title()
            morphology_status = (
                f"{operation}, {result.morphology.kernel_size}×"
                f"{result.morphology.kernel_size} kernel"
            )
        self.window.show_status(
            f"Current result — H {result.thresholds.lower_h_deg}.."
            f"{result.thresholds.upper_h_deg}°, "
            f"S {result.thresholds.lower_s_pct}..{result.thresholds.upper_s_pct}%, "
            f"V {result.thresholds.lower_v_pct}..{result.thresholds.upper_v_pct}%. "
            f"{morphology_status}."
        )
        if self.playback.state is PlaybackState.PLAYING:
            self.root.after_idle(self._schedule_video_frame)

    def _handle_export_completion(self, completion: WorkerCompletion) -> None:
        self._export_in_flight = False
        if completion.error is not None:
            message = format_recovery_message(
                completion.error,
                preserved_state=(
                    "The current input, thresholds, and result were preserved; no success was reported."
                ),
            )
            self.window.show_status(message)
            self._refresh_export_controls()
            messagebox.showerror("HSV Color Segmentation", message, parent=self.root)
        elif isinstance(completion.result, ExperimentReceipt):
            receipt = completion.result
            self.last_experiment_receipt = receipt
            self.window.show_status(
                f"Recorded experiment {receipt.run_id} at {receipt.record_path}."
            )
            self._refresh_export_controls()
        elif isinstance(completion.result, ExportReceipt):
            receipt = completion.result
            self.last_export_receipt = receipt
            frame = "" if receipt.frame_index is None else f", frame {receipt.frame_index}"
            self.window.show_status(
                f"Saved {receipt.kind} for {receipt.source_path.name}{frame} to {receipt.path}."
            )
            self._refresh_export_controls()
        if (
            self._resume_video_after_export
            and completion.request_revision == self._latest_request_revision
            and self.playback.play()
        ):
            self.window.update_video_controls(self.playback.state.value)
            self.root.after_idle(self._schedule_video_frame)
        self._resume_video_after_export = False

    def _handle_error(self, completion: WorkerCompletion) -> None:
        message = format_recovery_message(
            completion.error,
            preserved_state=self.session.preserved_state_description(),
        )
        self.window.set_loading(False)
        self.controls.set_enabled(True)
        self.morphology_controls.set_enabled(True)
        self.window.set_sampling_available(self.session.result is not None)
        if completion.kind in {"image", "video_open"} and self.session.result is not None:
            self._export_snapshot_valid = True
        self._refresh_export_controls()
        if completion.kind in {"video_frame", "video_restart"}:
            self.playback.mark_error(message)
        elif self._resume_video_on_failure and self.playback.play():
            self._resume_video_on_failure = False
            self.root.after_idle(self._schedule_video_frame)
        self.window.update_video_controls(self.playback.state.value)
        self.window.show_status(message)
        messagebox.showerror("HSV Color Segmentation", message, parent=self.root)

    def _accept_completion(
        self, completion: WorkerCompletion
    ) -> SegmentationResult | None:
        payload = completion.result
        if completion.kind == "image":
            if not isinstance(payload, SegmentationResult):
                return None
            self.playback.close()
            self.session.commit_candidate(payload)
            self.controls.set_thresholds(payload.thresholds)
            self.morphology_controls.set_settings(payload.morphology)
            return payload
        if completion.kind == "video_open":
            if not isinstance(payload, VideoCandidate):
                return None
            self.playback.commit_open(payload)
            self.controls.set_thresholds(payload.result.thresholds)
            self.morphology_controls.set_settings(payload.result.morphology)
            return payload.result
        if completion.kind == "video_frame":
            if not isinstance(payload, PlaybackAdvance):
                return None
            accepted = self.playback.commit_advance(payload)
            self.window.update_video_controls(self.playback.state.value)
            self.window.show_status(self.playback.status_message)
            if self.playback.state is PlaybackState.PLAYING:
                self.root.after_idle(self._schedule_video_frame)
            return payload.result if accepted else None
        if completion.kind == "video_restart":
            if not isinstance(payload, SegmentationResult):
                return None
            return payload if self.playback.commit_restart(payload) else None
        if not isinstance(payload, SegmentationResult):
            return None
        return payload if self.session.commit_result(payload) else None

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._poll_id is not None:
            try:
                self.root.after_cancel(self._poll_id)
            except tk.TclError:
                pass
        self.worker.shutdown()
        self.playback.close()
        self.root.destroy()


def run() -> None:
    root = tk.Tk()
    ApplicationController(root)
    root.mainloop()
