"""Bounded background processing with revision-carrying completions."""

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, SimpleQueue
from threading import RLock

import numpy as np

from ..io.images import load_image
from ..models import (
    HSVHistogram,
    HSVThresholdSet,
    MorphologySettings,
    ProcessingRequest,
    SegmentationResult,
)
from ..processing.color import rgb_to_hsv
from ..processing.histogram import compute_hsv_histogram
from ..processing.morphology import apply_morphology
from ..processing.segmentation import apply_mask, generate_mask
from .session import process_source


Processor = Callable[[ProcessingRequest], SegmentationResult]


@dataclass(frozen=True, slots=True)
class WorkerCompletion:
    """Plain data polled by the GUI thread; no worker callback touches Tk."""

    kind: str
    request_revision: int
    result: object | None = None
    error: BaseException | None = None


@dataclass(slots=True)
class _WorkItem:
    kind: str
    request_revision: int
    operation: Callable[[], object]
    cleanup: Callable[[object], None] | None = None
    replaceable: bool = True


class _CachedProcessor:
    """Reuse HSV while only thresholds change for one immutable source snapshot."""

    def __init__(self):
        self._source_identity: tuple[str, int | None, str] | None = None
        self._hsv: np.ndarray | None = None
        self._histogram: HSVHistogram | None = None

    def __call__(self, request: ProcessingRequest) -> SegmentationResult:
        identity = (request.session_id, request.frame_index, request.source.source_sha256)
        if identity != self._source_identity:
            self._hsv = rgb_to_hsv(request.rgb)
            self._histogram = compute_hsv_histogram(self._hsv)
            self._source_identity = identity
        hsv = self._hsv
        if hsv is None:  # Defensive guard for static analysis and future cache changes.
            raise RuntimeError("HSV cache was not initialized")
        histogram = self._histogram
        if histogram is None:
            raise RuntimeError("HSV histogram cache was not initialized")
        return process_source(
            request.source, request.thresholds, request.request_revision,
            hsv=hsv, histogram=histogram, morphology=request.morphology,
            analysis_settings=request.analysis_settings,
            watershed_settings=request.watershed_settings,
            ground_truth=request.ground_truth,
            evaluation_target=request.evaluation_target,
            settings_revision=request.settings_revision,
            segmentation_mode=request.segmentation_mode,
            grayscale_settings=request.grayscale_settings,
            threshold_ranges=request.threshold_ranges,
        )


class ProcessingWorker:
    """Run one job at a time and retain at most one replaceable pending job."""

    def __init__(self, processor: Processor | None = None):
        self._processor = processor or _CachedProcessor()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="hsv-processing")
        # add_done_callback may run synchronously when a very fast operation has
        # already completed. Re-entry keeps that completion from deadlocking the
        # submitter while preserving the same bounded state transitions.
        self._lock = RLock()
        self._active: Future[object] | None = None
        self._pending_required: _WorkItem | None = None
        self._pending: _WorkItem | None = None
        self._completions: SimpleQueue[WorkerCompletion] = SimpleQueue()
        self._closing = False

    @property
    def is_busy(self) -> bool:
        """Return whether active or queued work is still pending completion."""
        with self._lock:
            return (
                self._active is not None
                or self._pending_required is not None
                or self._pending is not None
            )

    def submit(self, request: ProcessingRequest) -> None:
        item = _WorkItem(
            "processing", request.request_revision,
            lambda: self._processor(request),
        )
        self._submit_item(item)

    def submit_image(
        self,
        path: str | Path,
        thresholds: HSVThresholdSet,
        request_revision: int,
        morphology: MorphologySettings | None = None,
        analysis_settings=None,
        watershed_settings=None,
        ground_truth=None,
        evaluation_target="baseline",
        settings_revision=0,
        segmentation_mode="hsv",
        grayscale_settings=None,
        threshold_ranges=(),
    ) -> None:
        def load_and_process() -> SegmentationResult:
            source = load_image(path)
            return process_source(
                source, thresholds, request_revision, morphology=morphology,
                analysis_settings=analysis_settings,
                watershed_settings=watershed_settings,
                ground_truth=ground_truth,
                evaluation_target=evaluation_target,
                settings_revision=settings_revision,
                segmentation_mode=segmentation_mode,
                grayscale_settings=grayscale_settings,
                threshold_ranges=threshold_ranges,
            )

        self._submit_item(_WorkItem("image", request_revision, load_and_process))

    def submit_operation(
        self, kind: str, request_revision: int, operation: Callable[[], object],
        *, cleanup: Callable[[object], None] | None = None,
        replace_pending: bool = True,
    ) -> None:
        """Serialize an application I/O operation through the bounded worker."""
        self._submit_item(
            _WorkItem(kind, request_revision, operation, cleanup, replace_pending)
        )

    def _submit_item(self, item: _WorkItem) -> None:
        with self._lock:
            if self._closing:
                return
            if self._active is None:
                self._start_locked(item)
            elif not item.replaceable:
                if self._pending_required is not None:
                    raise RuntimeError("a required background operation is already pending")
                self._pending_required = item
            else:
                self._pending = item

    def _start_locked(self, item: _WorkItem) -> None:
        future = self._executor.submit(item.operation)
        self._active = future
        future.add_done_callback(lambda completed: self._finish(item, completed))

    def _finish(self, item: _WorkItem, future: Future[object]) -> None:
        result = None
        error = None
        try:
            result = future.result()
        except BaseException as caught:
            error = caught
        with self._lock:
            closing = self._closing
            self._active = None
            if not self._closing and (
                self._pending_required is not None or self._pending is not None
            ):
                if self._pending_required is not None:
                    pending = self._pending_required
                    self._pending_required = None
                else:
                    pending = self._pending
                    self._pending = None
                self._start_locked(pending)
        if closing:
            if error is None and item.cleanup is not None:
                item.cleanup(result)
            return
        self._completions.put(
            WorkerCompletion(item.kind, item.request_revision, result=result, error=error)
        )

    def poll(self) -> list[WorkerCompletion]:
        completions = []
        while True:
            try:
                completions.append(self._completions.get_nowait())
            except Empty:
                return completions

    def shutdown(self) -> None:
        with self._lock:
            self._closing = True
            self._pending_required = None
            self._pending = None
        self._executor.shutdown(wait=False, cancel_futures=True)
