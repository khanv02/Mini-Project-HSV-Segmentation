"""Bounded sequential OpenCV video decoding at the file-I/O boundary."""

from collections.abc import Callable
from hashlib import sha256
import math
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np

from ..errors import DecodeError, InputError
from ..models import InputMedia, MAX_IMAGE_PIXELS


AMBIGUOUS_TERMINATION_MESSAGE = (
    "Video ended or the next frame could not be read; reopen or try a supported encoding."
)
SUPPORTED_VIDEO_MESSAGE = "choose a locally decodable MP4 or AVI video"


class VideoEnd(Exception):
    """A safe playback stop, either known EOF or backend-ambiguous termination."""

    def __init__(self, message: str, *, clean: bool):
        self.clean = clean
        super().__init__(message)


def _source_hash(path: Path) -> str:
    digest = sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise InputError(
            f"could not read the video; {SUPPORTED_VIDEO_MESSAGE}", path=path
        ) from error
    return digest.hexdigest()


class VideoReader:
    """Own one capture and expose immutable RGB frames from sequential decoding."""

    def __init__(
        self,
        path: Path,
        *,
        capture_factory: Callable[[str], object],
        session_id: str | None = None,
        trust_frame_count: bool = False,
    ):
        self.path = path
        self.source_format = "MP4" if path.suffix.lower() == ".mp4" else "AVI"
        self.source_sha256 = _source_hash(path)
        self.session_id = session_id or str(uuid4())
        self._capture_factory = capture_factory
        self._trust_frame_count = trust_frame_count
        self.capture = None
        self.backend = "OpenCV"
        self.frame_count_hint: int | None = None
        self._frame_index = -1
        self.closed = True
        self._open_capture()
        try:
            self.first_frame = self._decode_next(initial=True)
        except BaseException:
            self.release()
            raise

    @classmethod
    def open(
        cls, path: str | Path, *, capture_factory: Callable[[str], object] | None = None,
        trust_frame_count: bool = False,
    ) -> "VideoReader":
        source_path = Path(path).resolve()
        if source_path.suffix.lower() not in {".mp4", ".avi"}:
            raise InputError(
                f"unsupported video type; {SUPPORTED_VIDEO_MESSAGE}", path=source_path
            )
        factory = capture_factory or cv2.VideoCapture
        return cls(
            source_path,
            capture_factory=factory,
            trust_frame_count=trust_frame_count,
        )

    def _open_capture(self) -> None:
        try:
            capture = self._capture_factory(str(self.path))
        except Exception as error:
            raise InputError(
                f"could not open the video; {SUPPORTED_VIDEO_MESSAGE}", path=self.path
            ) from error
        self.capture = capture
        if capture is None or not capture.isOpened():
            if capture is not None:
                capture.release()
            self.closed = True
            raise InputError(
                f"video could not be opened; {SUPPORTED_VIDEO_MESSAGE}", path=self.path
            )
        self.closed = False
        try:
            backend = capture.getBackendName()
            if backend:
                self.backend = str(backend)
        except (AttributeError, cv2.error):
            self.backend = "OpenCV"
        count = float(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        rounded = round(count) if math.isfinite(count) else 0
        self.frame_count_hint = (
            int(rounded) if rounded > 0 and abs(count - rounded) < 1e-6 else None
        )
        self._frame_index = -1

    def _decode_next(self, *, initial: bool = False) -> InputMedia:
        next_index = self._frame_index + 1
        try:
            grabbed = bool(self.capture.grab())
        except (AttributeError, cv2.error) as error:
            raise DecodeError(
                f"could not acquire frame {next_index}", path=self.path
            ) from error
        if not grabbed:
            if initial:
                raise DecodeError(
                    "first frame could not be decoded; the video may be empty or unsupported",
                    path=self.path,
                )
            if self._trust_frame_count and self.frame_count_hint is not None:
                if next_index >= self.frame_count_hint:
                    raise VideoEnd("Video ended.", clean=True)
                raise DecodeError(
                    f"video stopped before the reported frame count at frame {next_index}",
                    path=self.path,
                )
            raise VideoEnd(AMBIGUOUS_TERMINATION_MESSAGE, clean=False)

        try:
            retrieved, bgr = self.capture.retrieve()
        except (AttributeError, cv2.error) as error:
            raise DecodeError(f"could not decode frame {next_index}", path=self.path) from error
        if not retrieved or bgr is None:
            raise DecodeError(f"could not decode frame {next_index}", path=self.path)
        if (
            not isinstance(bgr, np.ndarray)
            or bgr.dtype != np.uint8
            or bgr.ndim != 3
            or bgr.shape[2] != 3
            or min(bgr.shape[:2]) == 0
        ):
            raise DecodeError(
                f"frame {next_index} is not an 8-bit three-channel image", path=self.path
            )
        height, width = bgr.shape[:2]
        if height * width > MAX_IMAGE_PIXELS:
            raise InputError(
                f"frame exceeds the {MAX_IMAGE_PIXELS:,}-pixel limit; use a smaller video",
                path=self.path,
            )
        try:
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        except (cv2.error, MemoryError) as error:
            raise DecodeError(f"could not normalize frame {next_index}", path=self.path) from error
        self._frame_index = next_index
        return InputMedia(
            source_path=self.path,
            source_sha256=self.source_sha256,
            source_format=self.source_format,
            rgb=rgb,
            media_kind="video",
            session_id=self.session_id,
            frame_index=next_index,
            backend=self.backend,
        )

    def read_next(self) -> InputMedia:
        if self.closed:
            raise DecodeError("video reader is closed", path=self.path)
        return self._decode_next()

    def restart(self) -> InputMedia:
        """Release and reopen the file, retaining the logical video session id."""
        self.release()
        self._open_capture()
        try:
            self.first_frame = self._decode_next(initial=True)
        except BaseException:
            self.release()
            raise
        return self.first_frame

    def release(self) -> None:
        capture = self.capture
        self.capture = None
        self.closed = True
        if capture is not None:
            capture.release()

    def __enter__(self) -> "VideoReader":
        return self

    def __exit__(self, *_args) -> None:
        self.release()
