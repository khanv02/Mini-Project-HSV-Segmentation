"""Main-thread controller for still-image and sequential-video workflows."""

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
from ..models import HSVThresholdSet, ProcessingRequest, SegmentationResult
from .main_window import MainWindow
from .threshold_controls import ThresholdControls


class ApplicationController:
    """Connect dialogs/widgets to serialized application and I/O services."""

    POLL_MS = 25

    def __init__(self, root: tk.Tk):
        self.root = root
        self.window = MainWindow(root)
        self.session = ImageSession()
        self.playback = PlaybackSession(self.session)
        self.worker = ProcessingWorker()
        self.controls = ThresholdControls(
            self.window.parameter_section,
            initial=self.session.thresholds,
            on_valid=self._on_thresholds,
        )
        self._latest_request_revision = 0
        self._video_request_in_flight: int | None = None
        self._resume_video_on_failure = False
        self._closed = False
        self.window.set_commands(
            open_image=self.choose_image,
            open_video=self.choose_video,
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
        self.window.show_status("Parameters changed — result pending…")
        self.worker.submit(request)

    def _poll_worker(self) -> None:
        if self._closed:
            return
        for completion in self.worker.poll():
            self._handle_completion(completion)
        self._poll_id = self.root.after(self.POLL_MS, self._poll_worker)

    def _handle_completion(self, completion: WorkerCompletion) -> None:
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
        self.window.show_result(result)
        self.window.set_loading(False)
        self.controls.set_enabled(True)
        self.window.update_video_controls(self.playback.state.value)
        self.window.show_status(
            f"Current result — H {result.thresholds.lower_h_deg}.."
            f"{result.thresholds.upper_h_deg}°, "
            f"S {result.thresholds.lower_s_pct}..{result.thresholds.upper_s_pct}%, "
            f"V {result.thresholds.lower_v_pct}..{result.thresholds.upper_v_pct}%."
        )
        if self.playback.state is PlaybackState.PLAYING:
            self.root.after_idle(self._schedule_video_frame)

    def _handle_error(self, completion: WorkerCompletion) -> None:
        message = str(completion.error)
        self.window.set_loading(False)
        self.controls.set_enabled(True)
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
