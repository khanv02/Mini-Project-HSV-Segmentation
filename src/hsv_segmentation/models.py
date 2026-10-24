"""Shared in-memory data contracts; no GUI, codecs, or filesystem access.

Dimensions and result identity are derived from the source rather than repeated
as independently editable fields. Array snapshots use immutable bytes backing:
neither a caller's later mutation nor setflags(write=True) can change a snapshot.
"""

from dataclasses import dataclass, field
from numbers import Integral
from pathlib import Path
import re
from typing import Final, Literal
from uuid import uuid4

import numpy as np
from numpy.typing import NDArray

from .errors import ValidationError


MAX_IMAGE_PIXELS: Final = 12_000_000
THRESHOLD_FIELDS: Final = (
    "lower_h_deg", "upper_h_deg", "lower_s_pct", "upper_s_pct",
    "lower_v_pct", "upper_v_pct",
)
RGBImage = NDArray[np.uint8]
BinaryMask = NDArray[np.uint8]


def _bounded_integer(value, name: str, minimum: int, maximum: int | None = None) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise ValidationError(name, "must be an integer, not text, a fraction, or a boolean")
    if value < minimum or (maximum is not None and value > maximum):
        allowed = f"{minimum}..{maximum}" if maximum is not None else f">={minimum}"
        raise ValidationError(name, f"must be in {allowed}")
    return int(value)


def _nonempty_text(value, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(name, "must be nonempty text")


def validate_rgb(rgb: RGBImage) -> tuple[int, int]:
    """Check an RGB uint8 array without copying/casting; return (height, width)."""
    if not isinstance(rgb, np.ndarray) or rgb.dtype != np.uint8:
        raise ValidationError("rgb", "must be a uint8 NumPy array")
    if rgb.ndim != 3 or rgb.shape[2] != 3 or min(rgb.shape[:2]) == 0:
        raise ValidationError("rgb", "must have nonempty shape (height, width, 3)")
    height, width = rgb.shape[:2]
    if height * width > MAX_IMAGE_PIXELS:
        raise ValidationError("rgb", f"exceeds the {MAX_IMAGE_PIXELS:,}-pixel limit")
    return height, width


def _immutable_copy(array: np.ndarray) -> np.ndarray:
    # A write-disabled owning ndarray could be made writeable again. A bytes
    # buffer cannot; it also detaches noncontiguous views from their input owner.
    return np.frombuffer(array.tobytes(order="C"), dtype=array.dtype).reshape(array.shape)


@dataclass(frozen=True, slots=True)
class HSVThresholdSet:
    """Six inclusive bounds plus a revision; reversed hue wraps through zero."""

    lower_h_deg: int = 0
    upper_h_deg: int = 360
    lower_s_pct: int = 0
    upper_s_pct: int = 100
    lower_v_pct: int = 0
    upper_v_pct: int = 100
    parameter_revision: int = 0

    def __post_init__(self):
        maxima = (359, 360, 100, 100, 100, 100)
        for name, maximum in zip(THRESHOLD_FIELDS, maxima):
            value = _bounded_integer(getattr(self, name), name, 0, maximum)
            object.__setattr__(self, name, value)
        for lower, upper in (("lower_s_pct", "upper_s_pct"),
                             ("lower_v_pct", "upper_v_pct")):
            if getattr(self, lower) > getattr(self, upper):
                raise ValidationError(lower, f"must not exceed {upper}")
        revision = _bounded_integer(self.parameter_revision, "parameter_revision", 0)
        object.__setattr__(self, "parameter_revision", revision)

    @property
    def wraps_hue(self) -> bool:
        return self.lower_h_deg > self.upper_h_deg

    def as_dict(self) -> dict[str, int]:
        """Return just the six named numeric bounds for portable record metadata."""
        return {name: getattr(self, name) for name in THRESHOLD_FIELDS}


@dataclass(frozen=True, slots=True, eq=False)
class InputMedia:
    """One fully decoded image/frame, with trusted identity and owned RGB pixels.

    The I/O layer supplies the path/hash/format after decoding. This model only
    validates their representation: it never reads a path or computes a file hash.
    Video adapters must retain session_id when advancing to a subsequent frame.
    """

    source_path: Path
    source_sha256: str
    source_format: str
    rgb: RGBImage = field(repr=False)
    media_kind: Literal["image", "video"] = "image"
    session_id: str = field(default_factory=lambda: str(uuid4()))
    frame_index: int | None = None
    backend: str | None = None

    def __post_init__(self):
        _nonempty_text(self.session_id, "session_id")
        if not isinstance(self.source_path, (str, Path)):
            raise ValidationError("source_path", "must be an absolute local path")
        path = Path(self.source_path)
        if not path.is_absolute():
            raise ValidationError("source_path", "must be an absolute local path")
        object.__setattr__(self, "source_path", path)
        if not isinstance(self.source_sha256, str) or re.fullmatch(
                r"[0-9a-f]{64}", self.source_sha256) is None:
            raise ValidationError("source_sha256", "must be 64 lowercase hexadecimal characters")
        if self.media_kind not in ("image", "video"):
            raise ValidationError("media_kind", "must be image or video")
        formats = ("PNG", "JPEG", "BMP") if self.media_kind == "image" else ("MP4", "AVI")
        if self.source_format not in formats:
            raise ValidationError("source_format", f"must be one of {', '.join(formats)}")
        if self.media_kind == "image":
            if self.frame_index is not None:
                raise ValidationError("frame_index", "must be None for a still image")
            if self.backend is not None:
                raise ValidationError("backend", "must be None for a still image")
        else:
            index = _bounded_integer(self.frame_index, "frame_index", 0)
            object.__setattr__(self, "frame_index", index)
            _nonempty_text(self.backend, "backend")
        validate_rgb(self.rgb)
        object.__setattr__(self, "rgb", _immutable_copy(self.rgb))

    @property
    def height(self) -> int:
        return self.rgb.shape[0]

    @property
    def width(self) -> int:
        return self.rgb.shape[1]


def _validate_snapshot_identity(source, thresholds, request_revision) -> int:
    if not isinstance(source, InputMedia):
        raise ValidationError("source", "must be an InputMedia snapshot")
    if not isinstance(thresholds, HSVThresholdSet):
        raise ValidationError("thresholds", "must be an HSVThresholdSet snapshot")
    return _bounded_integer(request_revision, "request_revision", 0)


class _SnapshotIdentity:
    """Derived accessors avoid independently editable identity/revision copies."""

    __slots__ = ()

    @property
    def session_id(self) -> str:
        return self.source.session_id

    @property
    def frame_index(self) -> int | None:
        return self.source.frame_index

    @property
    def parameter_revision(self) -> int:
        return self.thresholds.parameter_revision


@dataclass(frozen=True, slots=True)
class ProcessingRequest(_SnapshotIdentity):
    """One source/frame and one accepted threshold revision for a future worker."""

    source: InputMedia
    thresholds: HSVThresholdSet
    request_revision: int = 0

    def __post_init__(self):
        revision = _validate_snapshot_identity(self.source, self.thresholds, self.request_revision)
        object.__setattr__(self, "request_revision", revision)

    @property
    def rgb(self) -> RGBImage:
        return self.source.rgb


@dataclass(frozen=True, slots=True, eq=False)
class SegmentationResult(_SnapshotIdentity):
    """One immutable result; source/frame and parameter identity cannot drift.

    Checks here validate representation and extraction consistency only. Whether
    a mask selects the correct HSV interval is verified by the Phase 3 algorithm.
    """

    source: InputMedia
    thresholds: HSVThresholdSet
    mask: BinaryMask = field(repr=False)
    segmented_rgb: RGBImage = field(repr=False)
    request_revision: int = 0

    def __post_init__(self):
        revision = _validate_snapshot_identity(self.source, self.thresholds, self.request_revision)
        object.__setattr__(self, "request_revision", revision)
        shape = (self.source.height, self.source.width)
        if (not isinstance(self.mask, np.ndarray) or self.mask.dtype != np.uint8
                or self.mask.shape != shape or not np.all((self.mask == 0) | (self.mask == 255))):
            raise ValidationError("mask", "must be source-sized uint8 with values only 0 or 255")
        if validate_rgb(self.segmented_rgb) != shape:
            raise ValidationError("segmented_rgb", "must match the source dimensions")
        selected = self.mask == 255
        if (np.any(self.segmented_rgb[~selected] != 0)
                or not np.array_equal(self.segmented_rgb[selected], self.source.rgb[selected])):
            raise ValidationError("segmented_rgb", "must preserve selected RGB and black out the rest")
        object.__setattr__(self, "mask", _immutable_copy(self.mask))
        object.__setattr__(self, "segmented_rgb", _immutable_copy(self.segmented_rgb))

    @property
    def original_rgb(self) -> RGBImage:
        return self.source.rgb

    @property
    def height(self) -> int:
        return self.source.height

    @property
    def width(self) -> int:
        return self.source.width
