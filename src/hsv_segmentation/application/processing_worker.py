"""Bounded background processing with revision-carrying completions."""

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, SimpleQueue
from threading import Lock

from ..io.images import load_image
from ..models import HSVThresholdSet, ProcessingRequest, SegmentationResult
from .session import process_source


Processor = Callable[[ProcessingRequest], SegmentationResult]


@dataclass(frozen=True, slots=True)
class WorkerCompletion:
    """Plain data polled by the GUI thread; no worker callback touches Tk."""

    kind: str
    request_revision: int
    result: SegmentationResult | None = None
    error: BaseException | None = None


@dataclass(slots=True)
class _WorkItem:
    kind: str
    request_revision: int
    operation: Callable[[], SegmentationResult]


def _default_processor(request: ProcessingRequest) -> SegmentationResult:
    return process_source(request.source, request.thresholds, request.request_revision)


class ProcessingWorker:
    """Run one job at a time and retain at most one replaceable pending job."""

    def __init__(self, processor: Processor | None = None):
        self._processor = processor or _default_processor
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="hsv-processing")
        self._lock = Lock()
        self._active: Future[SegmentationResult] | None = None
        self._pending: _WorkItem | None = None
        self._completions: SimpleQueue[WorkerCompletion] = SimpleQueue()
        self._closing = False

    def submit(self, request: ProcessingRequest) -> None:
        item = _WorkItem(
            "processing", request.request_revision,
            lambda: self._processor(request),
        )
        self._submit_item(item)

    def submit_image(
        self, path: str | Path, thresholds: HSVThresholdSet, request_revision: int
    ) -> None:
        def load_and_process() -> SegmentationResult:
            source = load_image(path)
            return process_source(source, thresholds, request_revision)

        self._submit_item(_WorkItem("image", request_revision, load_and_process))

    def _submit_item(self, item: _WorkItem) -> None:
        with self._lock:
            if self._closing:
                return
            if self._active is None:
                self._start_locked(item)
            else:
                self._pending = item

    def _start_locked(self, item: _WorkItem) -> None:
        future = self._executor.submit(item.operation)
        self._active = future
        future.add_done_callback(lambda completed: self._finish(item, completed))

    def _finish(self, item: _WorkItem, future: Future[SegmentationResult]) -> None:
        try:
            completion = WorkerCompletion(
                item.kind, item.request_revision, result=future.result()
            )
        except BaseException as error:
            completion = WorkerCompletion(item.kind, item.request_revision, error=error)
        self._completions.put(completion)
        with self._lock:
            self._active = None
            if not self._closing and self._pending is not None:
                pending = self._pending
                self._pending = None
                self._start_locked(pending)

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
            self._pending = None
        self._executor.shutdown(wait=False, cancel_futures=True)
