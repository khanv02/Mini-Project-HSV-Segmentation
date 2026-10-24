"""Video playback state transitions independent of Tk scheduling."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol

from ..io.video import VideoEnd, VideoReader
from ..models import HSVThresholdSet, InputMedia, SegmentationResult
from .session import ImageSession, process_source


class PlaybackState(Enum):
    EMPTY = "empty"
    PAUSED = "paused"
    PLAYING = "playing"
    ENDED = "ended"
    ERROR = "error"
    CLOSED = "closed"


class ReaderProtocol(Protocol):
    first_frame: InputMedia

    def read_next(self) -> InputMedia: ...
    def restart(self) -> InputMedia: ...
    def release(self) -> None: ...


@dataclass(frozen=True, slots=True)
class VideoCandidate:
    reader: ReaderProtocol
    result: SegmentationResult


@dataclass(frozen=True, slots=True)
class PlaybackAdvance:
    session_id: str
    result: SegmentationResult | None = None
    termination: VideoEnd | None = None


class PlaybackSession:
    """Own a video reader while sharing committed snapshots with the media session."""

    def __init__(self, media_session: ImageSession, *, reader_factory=VideoReader.open):
        self.media_session = media_session
        self._reader_factory = reader_factory
        self._reader: ReaderProtocol | None = None
        self.state = PlaybackState.EMPTY
        self.status_message = "No video loaded."

    @property
    def reader(self) -> ReaderProtocol | None:
        return self._reader

    @property
    def has_video(self) -> bool:
        return self._reader is not None and self.state is not PlaybackState.CLOSED

    def prepare_open(
        self, path: str | Path, thresholds: HSVThresholdSet, request_revision: int
    ) -> VideoCandidate:
        reader = self._reader_factory(path)
        try:
            result = process_source(reader.first_frame, thresholds, request_revision)
        except BaseException:
            reader.release()
            raise
        return VideoCandidate(reader, result)

    def commit_open(self, candidate: VideoCandidate) -> None:
        previous = self._reader
        self._reader = candidate.reader
        self.media_session.commit_candidate(candidate.result)
        self.state = PlaybackState.PAUSED
        self.status_message = "Video paused at frame 0."
        if previous is not None and previous is not candidate.reader:
            previous.release()

    def play(self) -> bool:
        if self.state is not PlaybackState.PAUSED:
            return False
        self.state = PlaybackState.PLAYING
        self.status_message = "Video playing."
        return True

    def pause(self) -> bool:
        if self.state is not PlaybackState.PLAYING:
            return False
        self.state = PlaybackState.PAUSED
        frame = self.media_session.source.frame_index if self.media_session.source else 0
        self.status_message = f"Video paused at frame {frame}."
        return True

    def prepare_next(
        self, thresholds: HSVThresholdSet, request_revision: int
    ) -> PlaybackAdvance:
        if self._reader is None:
            raise RuntimeError("no video reader is active")
        session_id = self._reader.first_frame.session_id
        try:
            frame = self._reader.read_next()
        except VideoEnd as termination:
            return PlaybackAdvance(session_id, termination=termination)
        return PlaybackAdvance(
            session_id,
            result=process_source(frame, thresholds, request_revision),
        )

    def commit_advance(self, advance: PlaybackAdvance) -> bool:
        current = self.media_session.source
        if current is None or advance.session_id != current.session_id:
            return False
        if advance.termination is not None:
            if advance.termination.clean:
                self.state = PlaybackState.ENDED
                self.status_message = str(advance.termination)
            else:
                self.state = PlaybackState.ENDED
                path = current.source_path
                self.status_message = (
                    f"Operation: decode next video frame. Affected: {path}. "
                    "Cause: uncertain decoder termination. "
                    f"Details: {advance.termination} "
                    "Preserved: The last valid video frame, thresholds, and result were preserved. "
                    "Action: Reopen the video or try a supported MP4/AVI encoding."
                )
            return False
        if advance.result is None or not self.media_session.commit_frame_result(advance.result):
            return False
        self.status_message = f"Video frame {advance.result.frame_index}."
        return True

    def reprocess_current(
        self, thresholds: HSVThresholdSet, request_revision: int
    ) -> SegmentationResult:
        source = self.media_session.source
        if source is None or source.media_kind != "video":
            raise RuntimeError("no video frame is available")
        return process_source(source, thresholds, request_revision)

    def prepare_restart(
        self, thresholds: HSVThresholdSet, request_revision: int
    ) -> SegmentationResult:
        if self._reader is None:
            raise RuntimeError("no video reader is active")
        return process_source(self._reader.restart(), thresholds, request_revision)

    def commit_restart(self, result: SegmentationResult) -> bool:
        if not self.media_session.commit_frame_result(result):
            return False
        self.state = PlaybackState.PAUSED
        self.status_message = "Video restarted and paused at frame 0."
        return True

    def mark_error(self, message: str) -> None:
        self.state = PlaybackState.ERROR
        self.status_message = message

    def close(self) -> None:
        reader = self._reader
        self._reader = None
        self.state = PlaybackState.CLOSED
        self.status_message = "Video closed."
        if reader is not None:
            reader.release()
