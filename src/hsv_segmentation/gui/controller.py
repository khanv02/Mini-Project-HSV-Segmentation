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
from ..models import HSVThresholdSet, ProcessingRequest, SegmentationResult
from .main_window import MainWindow
from .threshold_controls import ThresholdControls


class ApplicationController:
    """Connect dialogs/widgets to serialized application and I/O services."""

    POLL_MS = 25

    def __init__(
        self,
        root: tk.Tk,
        *,
        exporter: Callable[..., ExportReceipt] = export_snapshot,
    ):
        self.root = root
        self.window = MainWindow(root)
        self.session = ImageSession()
        self.playback = PlaybackSession(self.session)
        self.worker = ProcessingWorker()
        self._exporter = exporter
        self.controls = ThresholdControls(
            self.window.parameter_section,
            initial=self.session.thresholds,
            on_valid=self._on_thresholds,
            on_invalid=self._on_invalid_thresholds,
        )
        self._latest_request_revision = 0
        self._video_request_in_flight: int | None = None
        self._resume_video_on_failure = False
        self._resume_video_after_export = False
        self._export_in_flight = False
        self._export_snapshot_valid = False
        self.last_export_receipt: ExportReceipt | None = None
        self._closed = False
        self.window.set_commands(
            open_image=self.choose_image,
            open_video=self.choose_video,
            save_mask=self.choose_save_mask,
            save_result=self.choose_save_result,
            play=self.play_video,
            pause=self.pause_video,
            restart=self.restart_video,
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
        revision = self._next_revision(invalidate_video=True)
        self.window.set_loading(True)
        self.controls.set_enabled(False)
        self._export_snapshot_valid = False
        self._refresh_export_controls()
        self.window.show_status("Loading and processing image…")
        self.worker.submit_image(path, self.session.thresholds, revision)

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
        revision = self._next_revision(invalidate_video=True)
        thresholds = self.session.thresholds
        self.window.set_loading(True)
        self.controls.set_enabled(False)
        self._export_snapshot_valid = False
        self._refresh_export_controls()
        self.window.show_status("Opening video and decoding its first frame…")
        self.worker.submit_operation(
            "video_open", revision,
            lambda: self.playback.prepare_open(path, thresholds, revision),
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
        self.playback.pause()
        revision = self._next_revision(invalidate_video=True)
        thresholds = self.session.thresholds
        self._export_snapshot_valid = False
        self._refresh_export_controls()
        self.window.show_status("Restarting video…")
        self.worker.submit_operation(
            "video_restart", revision,
            lambda: self.playback.prepare_restart(thresholds, revision),
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
        self.worker.submit_operation(
            "video_frame", revision,
            lambda: self.playback.prepare_next(thresholds, revision),
        )

    def _on_thresholds(self, thresholds: HSVThresholdSet) -> None:
        self.session.accept_thresholds(thresholds)
        source = self.session.source
        if source is None:
            self.window.show_status("Thresholds ready — open an image or video.")
            return
        revision = self._next_revision(invalidate_video=True)
        request = ProcessingRequest(source, thresholds, revision)
        self._export_snapshot_valid = False
        self._refresh_export_controls()
        self.window.show_status("Parameters changed — result pending…")
        self.worker.submit(request)

    def _on_invalid_thresholds(self, error: ValidationError) -> None:
        self._export_snapshot_valid = False
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

    def _begin_export(self, kind: str, path: str | Path | None) -> bool:
        if path is None or str(path) == "":
            return False
        snapshot = self.session.result
        if (
            self._export_in_flight
            or not self._export_snapshot_valid
            or snapshot is None
            or snapshot.thresholds != self.session.thresholds
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
        )
        self.window.set_export_available(available)

    def _poll_worker(self) -> None:
        if self._closed:
            return
        for completion in self.worker.poll():
            self._handle_completion(completion)
        self._poll_id = self.root.after(self.POLL_MS, self._poll_worker)

    def _handle_completion(self, completion: WorkerCompletion) -> None:
        if completion.kind in {"export_mask", "export_result"}:
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
        self.window.update_video_controls(self.playback.state.value)
        self._refresh_export_controls()
        self.window.show_status(
            f"Current result — H {result.thresholds.lower_h_deg}.."
            f"{result.thresholds.upper_h_deg}°, "
            f"S {result.thresholds.lower_s_pct}..{result.thresholds.upper_s_pct}%, "
            f"V {result.thresholds.lower_v_pct}..{result.thresholds.upper_v_pct}%."
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
            return payload
        if completion.kind == "video_open":
            if not isinstance(payload, VideoCandidate):
                return None
            self.playback.commit_open(payload)
            self.controls.set_thresholds(payload.result.thresholds)
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
