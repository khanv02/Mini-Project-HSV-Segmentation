"""Main-thread controller for the still-image desktop workflow."""

import tkinter as tk
from tkinter import filedialog, messagebox

from ..application.processing_worker import ProcessingWorker, WorkerCompletion
from ..application.session import ImageSession
from ..models import HSVThresholdSet, ProcessingRequest
from .main_window import MainWindow
from .threshold_controls import ThresholdControls


class ApplicationController:
    """Connect dialogs/widgets to application and I/O services."""

    POLL_MS = 25

    def __init__(self, root: tk.Tk):
        self.root = root
        self.window = MainWindow(root)
        self.session = ImageSession()
        self.worker = ProcessingWorker()
        self.controls = ThresholdControls(
            self.window.parameter_section,
            initial=self.session.thresholds,
            on_valid=self._on_thresholds,
        )
        self._latest_request_revision = 0
        self._closed = False
        self.window.set_open_command(self.choose_image)
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
        self._latest_request_revision += 1
        revision = self._latest_request_revision
        self.window.set_loading(True)
        self.controls.set_enabled(False)
        self.window.show_status("Loading and processing image…")
        self.worker.submit_image(path, self.session.thresholds, revision)

    def _on_thresholds(self, thresholds: HSVThresholdSet) -> None:
        self.session.accept_thresholds(thresholds)
        source = self.session.source
        if source is None:
            self.window.show_status("Thresholds ready — open an image to segment.")
            return
        self._latest_request_revision += 1
        revision = self._latest_request_revision
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
        if completion.request_revision != self._latest_request_revision:
            return
        if completion.error is not None:
            self.window.set_loading(False)
            self.controls.set_enabled(True)
            self.window.show_status(str(completion.error))
            messagebox.showerror("HSV Color Segmentation", str(completion.error), parent=self.root)
            return
        if completion.result is None:
            return
        if completion.kind == "image":
            self.session.commit_candidate(completion.result)
            self.controls.set_thresholds(completion.result.thresholds)
        elif not self.session.commit_result(completion.result):
            return
        self.window.show_result(completion.result)
        self.window.set_loading(False)
        self.controls.set_enabled(True)
        self.window.show_status(
            f"Current result — H {completion.result.thresholds.lower_h_deg}.."
            f"{completion.result.thresholds.upper_h_deg}°, "
            f"S {completion.result.thresholds.lower_s_pct}.."
            f"{completion.result.thresholds.upper_s_pct}%, "
            f"V {completion.result.thresholds.lower_v_pct}.."
            f"{completion.result.thresholds.upper_v_pct}%."
        )

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
        self.root.destroy()


def run() -> None:
    root = tk.Tk()
    ApplicationController(root)
    root.mainloop()
