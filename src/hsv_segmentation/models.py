"""Shared in-memory data contracts; no GUI, codecs, or filesystem access.

Dimensions and result identity are derived from the source rather than repeated
as independently editable fields. Array snapshots use immutable bytes backing:
neither a caller's later mutation nor setflags(write=True) can change a snapshot.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from numbers import Integral, Real
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


class SegmentationMode(StrEnum):
    """Explicit mask-generation workflow; HSV remains the compatible default."""

    HSV = "hsv"
    GRAYSCALE = "grayscale"


def _boolean(value, name: str) -> bool:
    if not isinstance(value, (bool, np.bool_)):
        raise ValidationError(name, "must be a boolean")
    return bool(value)


@dataclass(frozen=True, slots=True)
class MorphologySettings:
    """Optional binary-mask cleanup applied after exact HSV thresholding."""

    enabled: bool = False
    operation: Literal["opening", "closing", "opening_closing"] = "opening"
    kernel_size: int = 3

    def __post_init__(self):
        if not isinstance(self.enabled, bool):
            raise ValidationError("enabled", "must be a boolean")
        if (
            not isinstance(self.operation, str)
            or self.operation not in {"opening", "closing", "opening_closing"}
        ):
            raise ValidationError(
                "operation", "must be opening, closing, or opening_closing"
            )
        if isinstance(self.kernel_size, bool) or self.kernel_size not in {3, 5, 7, 9}:
            raise ValidationError("kernel_size", "must be one of 3, 5, 7, or 9")

    def as_dict(self) -> dict[str, bool | str | int]:
        return {
            "enabled": self.enabled,
            "operation": self.operation,
            "kernel_size": self.kernel_size,
        }


@dataclass(frozen=True, slots=True)
class AnalysisSettings:
    """Optional measurements derived from the current HSV/morphology mask."""

    enabled: bool = False
    connectivity: Literal[4, 8] = 8
    min_area_px: int = 0

    def __post_init__(self):
        object.__setattr__(self, "enabled", _boolean(self.enabled, "analysis.enabled"))
        if isinstance(self.connectivity, (bool, np.bool_)) or self.connectivity not in {4, 8}:
            raise ValidationError("connectivity", "must be 4 or 8")
        object.__setattr__(self, "connectivity", int(self.connectivity))
        object.__setattr__(
            self, "min_area_px", _bounded_integer(self.min_area_px, "min_area_px", 0)
        )

    def as_dict(self) -> dict[str, bool | int]:
        return {
            "enabled": self.enabled,
            "connectivity": self.connectivity,
            "min_area_px": self.min_area_px,
        }


@dataclass(frozen=True, slots=True)
class WatershedSettings:
    """Explicit marker-controlled separation parameters."""

    enabled: bool = False
    seed_fraction: float = 0.5
    background_iterations: int = 1
    kernel_size: int = 3

    def __post_init__(self):
        object.__setattr__(self, "enabled", _boolean(self.enabled, "watershed.enabled"))
        value = self.seed_fraction
        if (
            isinstance(value, (bool, np.bool_))
            or not isinstance(value, Real)
            or not np.isfinite(value)
            or not 0.0 < float(value) < 1.0
        ):
            raise ValidationError("seed_fraction", "must be finite and strictly between 0 and 1")
        object.__setattr__(self, "seed_fraction", float(value))
        object.__setattr__(self, "background_iterations", _bounded_integer(
            self.background_iterations, "background_iterations", 0, 10
        ))
        if isinstance(self.kernel_size, bool) or self.kernel_size not in {3, 5, 7, 9}:
            raise ValidationError("kernel_size", "must be one of 3, 5, 7, or 9")
        object.__setattr__(self, "kernel_size", int(self.kernel_size))

    def as_dict(self) -> dict[str, bool | int | float]:
        return {
            "enabled": self.enabled,
            "seed_fraction": self.seed_fraction,
            "background_iterations": self.background_iterations,
            "kernel_size": self.kernel_size,
        }


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


def _validate_binary_mask(mask: np.ndarray, name: str, shape=None) -> tuple[int, int]:
    if (
        not isinstance(mask, np.ndarray)
        or mask.dtype != np.uint8
        or mask.ndim != 2
        or min(mask.shape, default=0) == 0
        or not np.all((mask == 0) | (mask == 255))
        or (shape is not None and mask.shape != shape)
    ):
        suffix = f" with shape {shape}" if shape is not None else ""
        raise ValidationError(name, f"must be a nonempty binary uint8 array{suffix}")
    if mask.size > MAX_IMAGE_PIXELS:
        raise ValidationError(name, f"exceeds the {MAX_IMAGE_PIXELS:,}-pixel limit")
    return mask.shape


@dataclass(frozen=True, slots=True, eq=False)
class RegionStatistics:
    region_id: int
    area_px: int
    centroid_x: float
    centroid_y: float
    box: tuple[int, int, int, int]
    contours: tuple[np.ndarray, ...] = field(default_factory=tuple, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "region_id", _bounded_integer(self.region_id, "region_id", 1))
        object.__setattr__(self, "area_px", _bounded_integer(self.area_px, "area_px", 1))
        for name in ("centroid_x", "centroid_y"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value):
                raise ValidationError(name, "must be a finite coordinate")
            object.__setattr__(self, name, float(value))
        if (
            not isinstance(self.box, tuple) or len(self.box) != 4
            or any(isinstance(v, bool) or not isinstance(v, Integral) for v in self.box)
            or self.box[0] < 0 or self.box[1] < 0 or self.box[2] <= 0 or self.box[3] <= 0
        ):
            raise ValidationError("box", "must be (x, y, positive width, positive height)")
        object.__setattr__(self, "box", tuple(int(v) for v in self.box))
        normalized = []
        for contour in self.contours:
            if not isinstance(contour, np.ndarray) or contour.dtype != np.int32:
                raise ValidationError("contours", "must contain int32 point arrays")
            if contour.ndim != 3 or contour.shape[1:] != (1, 2) or contour.shape[0] == 0:
                raise ValidationError("contours", "must use OpenCV shape (points, 1, 2)")
            normalized.append(_immutable_copy(contour))
        object.__setattr__(self, "contours", tuple(normalized))

    def as_dict(self) -> dict:
        return {
            "id": self.region_id,
            "area_px": self.area_px,
            "centroid": [self.centroid_x, self.centroid_y],
            "box": list(self.box),
        }


@dataclass(frozen=True, slots=True, eq=False)
class RegionAnalysis:
    labels: NDArray[np.int32] = field(repr=False)
    filtered_mask: BinaryMask = field(repr=False)
    raw_count: int = 0
    regions: tuple[RegionStatistics, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if (
            not isinstance(self.labels, np.ndarray)
            or self.labels.dtype != np.int32
            or self.labels.ndim != 2
            or min(self.labels.shape, default=0) == 0
            or np.any(self.labels < 0)
        ):
            raise ValidationError("labels", "must be a nonempty nonnegative int32 array")
        _validate_binary_mask(self.filtered_mask, "filtered_mask", self.labels.shape)
        raw = _bounded_integer(self.raw_count, "raw_count", 0)
        if raw < len(self.regions):
            raise ValidationError("raw_count", "must be at least the retained region count")
        ids = tuple(region.region_id for region in self.regions)
        if ids != tuple(range(1, len(ids) + 1)):
            raise ValidationError("regions", "must use contiguous IDs starting at 1")
        expected = self.labels > 0
        if not np.array_equal(self.filtered_mask == 255, expected):
            raise ValidationError("filtered_mask", "must select exactly positive labels")
        actual_ids = set(np.unique(self.labels))
        expected_ids = set(range(1, len(ids) + 1))
        if actual_ids not in (expected_ids, expected_ids | {0}):
            raise ValidationError("labels", "must contain exactly background and retained IDs")
        object.__setattr__(self, "raw_count", raw)
        object.__setattr__(self, "labels", _immutable_copy(self.labels))
        object.__setattr__(self, "filtered_mask", _immutable_copy(self.filtered_mask))

    @property
    def retained_count(self) -> int:
        return len(self.regions)


@dataclass(frozen=True, slots=True, eq=False)
class WatershedResult:
    status: Literal["applied", "empty", "not_applied"]
    labels: NDArray[np.int32] = field(repr=False)
    boundaries: BinaryMask = field(repr=False)
    foreground_mask: BinaryMask = field(repr=False)
    reason: str | None = None
    analysis: RegionAnalysis | None = None

    def __post_init__(self):
        if self.status not in {"applied", "empty", "not_applied"}:
            raise ValidationError("watershed.status", "must be applied, empty, or not_applied")
        if not isinstance(self.labels, np.ndarray) or self.labels.dtype != np.int32:
            raise ValidationError("watershed.labels", "must be an int32 array")
        if self.labels.ndim != 2 or min(self.labels.shape, default=0) == 0 or np.any(self.labels < 0):
            raise ValidationError("watershed.labels", "must be nonempty and nonnegative")
        _validate_binary_mask(self.boundaries, "watershed.boundaries", self.labels.shape)
        _validate_binary_mask(self.foreground_mask, "watershed.foreground", self.labels.shape)
        if not np.array_equal(self.foreground_mask == 255, self.labels > 0):
            raise ValidationError("watershed.foreground", "must select positive labels")
        if self.status == "applied" and self.reason is not None:
            raise ValidationError("watershed.reason", "must be absent when applied")
        if self.status != "applied" and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValidationError("watershed.reason", "is required when separation was not applied")
        if self.analysis is not None and self.analysis.labels.shape != self.labels.shape:
            raise ValidationError("watershed.analysis", "must match labels")
        object.__setattr__(self, "labels", _immutable_copy(self.labels))
        object.__setattr__(self, "boundaries", _immutable_copy(self.boundaries))
        object.__setattr__(self, "foreground_mask", _immutable_copy(self.foreground_mask))


@dataclass(frozen=True, slots=True, eq=False)
class GroundTruth:
    mask: BinaryMask = field(repr=False)
    source_path: Path
    source_sha256: str
    pixel_sha256: str
    threshold: int
    alpha_ignored: bool
    session_id: str
    source_image_sha256: str
    frame_index: int | None
    truth_revision: int = 0

    def __post_init__(self):
        _validate_binary_mask(self.mask, "ground_truth.mask")
        path = Path(self.source_path)
        if not path.is_absolute():
            raise ValidationError("ground_truth.path", "must be absolute")
        object.__setattr__(self, "source_path", path)
        for name in ("source_sha256", "pixel_sha256", "source_image_sha256"):
            value = getattr(self, name)
            if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
                raise ValidationError(name, "must be 64 lowercase hexadecimal characters")
        object.__setattr__(self, "threshold", _bounded_integer(self.threshold, "truth_threshold", 0, 254))
        object.__setattr__(self, "alpha_ignored", _boolean(self.alpha_ignored, "alpha_ignored"))
        _nonempty_text(self.session_id, "ground_truth.session_id")
        if self.frame_index is not None:
            object.__setattr__(self, "frame_index", _bounded_integer(self.frame_index, "frame_index", 0))
        object.__setattr__(self, "truth_revision", _bounded_integer(self.truth_revision, "truth_revision", 0))
        object.__setattr__(self, "mask", _immutable_copy(self.mask))


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    target: Literal["baseline", "components", "watershed"]
    true_positive: int
    false_positive: int
    false_negative: int
    true_negative: int
    iou: float
    dice: float
    status: Literal["normal", "both_empty", "one_empty"] = "normal"

    def __post_init__(self):
        if self.target not in {"baseline", "components", "watershed"}:
            raise ValidationError("target", "must be baseline, components, or watershed")
        for name in ("true_positive", "false_positive", "false_negative", "true_negative"):
            object.__setattr__(self, name, _bounded_integer(getattr(self, name), name, 0))
        for name in ("iou", "dice"):
            value = getattr(self, name)
            if not isinstance(value, Real) or not np.isfinite(value) or not 0 <= value <= 1:
                raise ValidationError(name, "must be finite and in 0..1")
            object.__setattr__(self, name, float(value))
        if self.status not in {"normal", "both_empty", "one_empty"}:
            raise ValidationError("evaluation.status", "is invalid")

    def as_dict(self) -> dict:
        return {
            "target": self.target, "true_positive": self.true_positive,
            "false_positive": self.false_positive, "false_negative": self.false_negative,
            "true_negative": self.true_negative, "iou": self.iou, "dice": self.dice,
            "status": self.status,
        }


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
                raise ValidationError(
                    lower,
                    f"ordering rule requires {lower} <= {upper} (both 0..100)",
                )
        revision = _bounded_integer(self.parameter_revision, "parameter_revision", 0)
        object.__setattr__(self, "parameter_revision", revision)

    @property
    def wraps_hue(self) -> bool:
        return self.lower_h_deg > self.upper_h_deg

    def as_dict(self) -> dict[str, int]:
        """Return just the six named numeric bounds for portable record metadata."""
        return {name: getattr(self, name) for name in THRESHOLD_FIELDS}


@dataclass(frozen=True, slots=True, eq=False)
class HSVHistogram:
    """Immutable source/frame HSV distributions, independent of thresholds."""

    hue_counts: NDArray[np.int64] = field(repr=False)
    saturation_counts: NDArray[np.int64] = field(repr=False)
    value_counts: NDArray[np.int64] = field(repr=False)
    excluded_hue_count: int = 0

    def __post_init__(self):
        arrays = (
            ("hue_counts", self.hue_counts, 360),
            ("saturation_counts", self.saturation_counts, 101),
            ("value_counts", self.value_counts, 101),
        )
        for name, counts, size in arrays:
            if (
                not isinstance(counts, np.ndarray)
                or counts.dtype != np.int64
                or counts.shape != (size,)
                or np.any(counts < 0)
            ):
                raise ValidationError(
                    name, f"must be a nonnegative int64 array with shape ({size},)"
                )
            object.__setattr__(self, name, _immutable_copy(counts))
        excluded = _bounded_integer(
            self.excluded_hue_count, "excluded_hue_count", 0
        )
        object.__setattr__(self, "excluded_hue_count", excluded)
        pixel_count = int(self.saturation_counts.sum())
        if int(self.value_counts.sum()) != pixel_count:
            raise ValidationError("value_counts", "total must equal saturation total")
        if int(self.hue_counts.sum()) + excluded != pixel_count:
            raise ValidationError(
                "hue_counts", "total plus excluded hue count must equal pixel count"
            )

    @property
    def pixel_count(self) -> int:
        return int(self.saturation_counts.sum())

    @property
    def included_hue_count(self) -> int:
        return int(self.hue_counts.sum())


@dataclass(frozen=True, slots=True)
class GrayscaleSettings:
    """Validated user intent for one-sided intensity thresholding."""

    threshold_source: Literal["manual", "otsu"] = "manual"
    manual_threshold: int = 128
    polarity: Literal["bright", "dark"] = "bright"
    settings_revision: int = 0

    def __post_init__(self):
        if self.threshold_source not in {"manual", "otsu"}:
            raise ValidationError("threshold_source", "must be manual or otsu")
        object.__setattr__(self, "manual_threshold", _bounded_integer(
            self.manual_threshold, "manual_threshold", 0, 255
        ))
        if self.polarity not in {"bright", "dark"}:
            raise ValidationError("polarity", "must be bright or dark")
        object.__setattr__(self, "settings_revision", _bounded_integer(
            self.settings_revision, "grayscale.settings_revision", 0
        ))

    def as_dict(self, *, resolved_threshold: int | None = None) -> dict:
        threshold = self.manual_threshold if resolved_threshold is None else _bounded_integer(
            resolved_threshold, "threshold", 0, 255
        )
        return {
            "threshold_source": self.threshold_source,
            "threshold": threshold,
            "manual_threshold": self.manual_threshold,
            "polarity": self.polarity,
            "settings_revision": self.settings_revision,
        }


@dataclass(frozen=True, slots=True)
class GrayscaleEligibility:
    """Exact RGB channel-equality result bound to a source/frame."""

    eligible: bool
    source_sha256: str
    frame_index: int | None = None
    reason: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "eligible", _boolean(self.eligible, "eligible"))
        if re.fullmatch(r"[0-9a-f]{64}", self.source_sha256 or "") is None:
            raise ValidationError("source_sha256", "must be 64 lowercase hexadecimal characters")
        if self.frame_index is not None:
            object.__setattr__(self, "frame_index", _bounded_integer(
                self.frame_index, "frame_index", 0
            ))
        if self.eligible and self.reason is not None:
            raise ValidationError("reason", "must be absent when eligible")
        if not self.eligible and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValidationError("reason", "is required when ineligible")


@dataclass(frozen=True, slots=True)
class OtsuOutcome:
    """Deterministic threshold result or an honest unavailable state."""

    status: Literal["applied", "unavailable", "not_requested"] = "not_requested"
    source_sha256: str | None = None
    frame_index: int | None = None
    threshold: int | None = None
    reason: str | None = None
    tie_rule: str = "smallest_optimal_threshold"

    def __post_init__(self):
        if self.status not in {"applied", "unavailable", "not_requested"}:
            raise ValidationError("otsu.status", "is invalid")
        if self.source_sha256 is not None and re.fullmatch(
            r"[0-9a-f]{64}", self.source_sha256
        ) is None:
            raise ValidationError("source_sha256", "must be 64 lowercase hexadecimal characters")
        if self.frame_index is not None:
            object.__setattr__(self, "frame_index", _bounded_integer(
                self.frame_index, "frame_index", 0
            ))
        if self.status == "applied":
            if self.source_sha256 is None:
                raise ValidationError("source_sha256", "is required when Otsu is applied")
            object.__setattr__(self, "threshold", _bounded_integer(
                self.threshold, "otsu.threshold", 0, 254
            ))
            if self.reason is not None:
                raise ValidationError("otsu.reason", "must be absent when applied")
        elif self.status == "unavailable":
            if self.source_sha256 is None:
                raise ValidationError("source_sha256", "is required when Otsu is unavailable")
            if self.threshold is not None:
                raise ValidationError("otsu.threshold", "must be absent when unavailable")
            _nonempty_text(self.reason, "otsu.reason")
        elif self.threshold is not None or self.reason is not None:
            raise ValidationError("otsu", "not_requested cannot contain a result")
        if self.tie_rule != "smallest_optimal_threshold":
            raise ValidationError("tie_rule", "must be smallest_optimal_threshold")


@dataclass(frozen=True, slots=True)
class OverlayDisplaySettings:
    """All pixel-affecting choices for the dedicated Overlay preview."""

    variant: Literal["segmentation", "object_analysis", "watershed", "confusion"] = "segmentation"
    tint_color: tuple[int, int, int] = (0, 255, 80)
    opacity: float = 0.35
    contours: bool = True
    boxes: bool = True
    display_revision: int = 0

    def __post_init__(self):
        if self.variant not in {"segmentation", "object_analysis", "watershed", "confusion"}:
            raise ValidationError("overlay.variant", "is invalid")
        if (not isinstance(self.tint_color, tuple) or len(self.tint_color) != 3
                or any(isinstance(v, bool) or not isinstance(v, Integral) or not 0 <= v <= 255
                       for v in self.tint_color)):
            raise ValidationError("tint_color", "must contain three integers in 0..255")
        object.__setattr__(self, "tint_color", tuple(int(v) for v in self.tint_color))
        if isinstance(self.opacity, bool) or not isinstance(self.opacity, Real) or not 0 <= self.opacity <= 1:
            raise ValidationError("opacity", "must be a number in 0..1")
        object.__setattr__(self, "opacity", float(self.opacity))
        object.__setattr__(self, "contours", _boolean(self.contours, "contours"))
        object.__setattr__(self, "boxes", _boolean(self.boxes, "boxes"))
        object.__setattr__(self, "display_revision", _bounded_integer(
            self.display_revision, "display_revision", 0
        ))

    def as_dict(self) -> dict:
        return {
            "variant": self.variant, "tint_color": list(self.tint_color),
            "opacity": self.opacity, "contours": self.contours, "boxes": self.boxes,
            "display_revision": self.display_revision,
        }


@dataclass(frozen=True, slots=True, eq=False)
class OverlaySnapshot:
    """Exact immutable source-sized pixels captured from the Overlay contract."""

    rgb: RGBImage = field(repr=False)
    variant: Literal["segmentation", "object_analysis", "watershed", "confusion"]
    display_settings: OverlayDisplaySettings
    source_path: Path
    source_sha256: str
    session_id: str
    frame_index: int | None = None
    request_revision: int = 0
    settings_revision: int = 0
    truth_pixel_sha256: str | None = None

    def __post_init__(self):
        validate_rgb(self.rgb)
        if not isinstance(self.display_settings, OverlayDisplaySettings):
            raise ValidationError("display_settings", "must be OverlayDisplaySettings")
        if self.variant != self.display_settings.variant:
            raise ValidationError("overlay.variant", "must match display settings")
        path = Path(self.source_path)
        if not path.is_absolute():
            raise ValidationError("source_path", "must be absolute")
        object.__setattr__(self, "source_path", path)
        if re.fullmatch(r"[0-9a-f]{64}", self.source_sha256 or "") is None:
            raise ValidationError("source_sha256", "must be 64 lowercase hexadecimal characters")
        _nonempty_text(self.session_id, "session_id")
        if self.frame_index is not None:
            object.__setattr__(self, "frame_index", _bounded_integer(self.frame_index, "frame_index", 0))
        for name in ("request_revision", "settings_revision"):
            object.__setattr__(self, name, _bounded_integer(getattr(self, name), name, 0))
        if self.variant == "confusion" and re.fullmatch(
            r"[0-9a-f]{64}", self.truth_pixel_sha256 or ""
        ) is None:
            raise ValidationError("truth_pixel_sha256", "is required for confusion overlay")
        object.__setattr__(self, "rgb", _immutable_copy(self.rgb))


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
    morphology: MorphologySettings = field(default_factory=MorphologySettings)
    analysis_settings: AnalysisSettings = field(default_factory=AnalysisSettings)
    watershed_settings: WatershedSettings = field(default_factory=WatershedSettings)
    ground_truth: GroundTruth | None = field(default=None, repr=False)
    evaluation_target: Literal["baseline", "components", "watershed"] = "baseline"
    settings_revision: int = 0
    segmentation_mode: SegmentationMode = SegmentationMode.HSV
    grayscale_settings: GrayscaleSettings = field(default_factory=GrayscaleSettings)

    def __post_init__(self):
        revision = _validate_snapshot_identity(self.source, self.thresholds, self.request_revision)
        object.__setattr__(self, "request_revision", revision)
        if not isinstance(self.morphology, MorphologySettings):
            raise ValidationError("morphology", "must be MorphologySettings")
        if not isinstance(self.analysis_settings, AnalysisSettings):
            raise ValidationError("analysis_settings", "must be AnalysisSettings")
        if not isinstance(self.watershed_settings, WatershedSettings):
            raise ValidationError("watershed_settings", "must be WatershedSettings")
        if self.ground_truth is not None:
            if not isinstance(self.ground_truth, GroundTruth):
                raise ValidationError("ground_truth", "must be GroundTruth or None")
            if self.ground_truth.mask.shape != (self.source.height, self.source.width):
                raise ValidationError("ground_truth", "must match source dimensions")
        if self.evaluation_target not in {"baseline", "components", "watershed"}:
            raise ValidationError("evaluation_target", "is invalid")
        object.__setattr__(self, "settings_revision", _bounded_integer(
            self.settings_revision, "settings_revision", 0
        ))
        try:
            object.__setattr__(self, "segmentation_mode", SegmentationMode(self.segmentation_mode))
        except (TypeError, ValueError) as error:
            raise ValidationError("segmentation_mode", "must be hsv or grayscale") from error
        if not isinstance(self.grayscale_settings, GrayscaleSettings):
            raise ValidationError("grayscale_settings", "must be GrayscaleSettings")

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
    histogram: HSVHistogram | None = field(default=None, repr=False)
    morphology: MorphologySettings = field(default_factory=MorphologySettings)
    original_mask: BinaryMask | None = field(default=None, repr=False)
    analysis_settings: AnalysisSettings = field(default_factory=AnalysisSettings)
    watershed_settings: WatershedSettings = field(default_factory=WatershedSettings)
    analysis: RegionAnalysis | None = field(default=None, repr=False)
    watershed: WatershedResult | None = field(default=None, repr=False)
    ground_truth: GroundTruth | None = field(default=None, repr=False)
    evaluation_target: Literal["baseline", "components", "watershed"] = "baseline"
    evaluation: EvaluationResult | None = None
    settings_revision: int = 0
    segmentation_mode: SegmentationMode = SegmentationMode.HSV
    grayscale_settings: GrayscaleSettings = field(default_factory=GrayscaleSettings)
    grayscale_eligibility: GrayscaleEligibility | None = None
    otsu_outcome: OtsuOutcome = field(default_factory=OtsuOutcome)

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
        if self.histogram is not None and not isinstance(self.histogram, HSVHistogram):
            raise ValidationError("histogram", "must be an HSVHistogram or None")
        if not isinstance(self.morphology, MorphologySettings):
            raise ValidationError("morphology", "must be MorphologySettings")
        original_mask = self.mask if self.original_mask is None else self.original_mask
        if (
            not isinstance(original_mask, np.ndarray)
            or original_mask.dtype != np.uint8
            or original_mask.shape != shape
            or not np.all((original_mask == 0) | (original_mask == 255))
        ):
            raise ValidationError(
                "original_mask", "must be a source-sized binary uint8 mask"
            )
        if not self.morphology.enabled and not np.array_equal(original_mask, self.mask):
            raise ValidationError(
                "original_mask", "must equal mask when morphology is disabled"
            )
        object.__setattr__(self, "original_mask", _immutable_copy(original_mask))
        if not isinstance(self.analysis_settings, AnalysisSettings):
            raise ValidationError("analysis_settings", "must be AnalysisSettings")
        if not isinstance(self.watershed_settings, WatershedSettings):
            raise ValidationError("watershed_settings", "must be WatershedSettings")
        if self.analysis is not None and self.analysis.labels.shape != shape:
            raise ValidationError("analysis", "must match source dimensions")
        if self.watershed is not None and self.watershed.labels.shape != shape:
            raise ValidationError("watershed", "must match source dimensions")
        if self.ground_truth is not None and self.ground_truth.mask.shape != shape:
            raise ValidationError("ground_truth", "must match source dimensions")
        if self.evaluation_target not in {"baseline", "components", "watershed"}:
            raise ValidationError("evaluation_target", "is invalid")
        if self.evaluation is not None and self.evaluation.target != self.evaluation_target:
            raise ValidationError("evaluation", "target must match evaluation_target")
        object.__setattr__(self, "settings_revision", _bounded_integer(
            self.settings_revision, "settings_revision", 0
        ))
        try:
            object.__setattr__(self, "segmentation_mode", SegmentationMode(self.segmentation_mode))
        except (TypeError, ValueError) as error:
            raise ValidationError("segmentation_mode", "must be hsv or grayscale") from error
        if not isinstance(self.grayscale_settings, GrayscaleSettings):
            raise ValidationError("grayscale_settings", "must be GrayscaleSettings")
        if self.grayscale_eligibility is not None and not isinstance(
            self.grayscale_eligibility, GrayscaleEligibility
        ):
            raise ValidationError("grayscale_eligibility", "must be GrayscaleEligibility or None")
        if not isinstance(self.otsu_outcome, OtsuOutcome):
            raise ValidationError("otsu_outcome", "must be OtsuOutcome")
        if self.segmentation_mode is SegmentationMode.GRAYSCALE:
            if self.grayscale_eligibility is None or not self.grayscale_eligibility.eligible:
                raise ValidationError("segmentation_mode", "grayscale requires eligible source pixels")
            if self.grayscale_eligibility.source_sha256 != self.source.source_sha256:
                raise ValidationError("grayscale_eligibility", "must match source identity")
            if self.grayscale_settings.threshold_source == "otsu" and self.otsu_outcome.status != "applied":
                raise ValidationError("otsu_outcome", "must be applied for an Otsu result")

    @property
    def original_rgb(self) -> RGBImage:
        return self.source.rgb

    @property
    def height(self) -> int:
        return self.source.height

    @property
    def width(self) -> int:
        return self.source.width

    @property
    def selected_pixel_count(self) -> int:
        return int(np.count_nonzero(self.mask))

    @property
    def selected_pixel_percentage(self) -> float:
        return self.selected_pixel_count * 100.0 / self.mask.size
