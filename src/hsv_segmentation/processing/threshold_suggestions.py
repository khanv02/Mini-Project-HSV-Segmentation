"""Pure helpers for color sampling, suggested ranges, and common presets."""

from dataclasses import dataclass
import math
from types import MappingProxyType

import numpy as np

from ..errors import ValidationError
from ..models import HSVThresholdSet, validate_rgb
from .color import rgb_to_hsv


@dataclass(frozen=True, slots=True)
class ColorSample:
    """One source pixel represented in both RGB and user-facing HSV units."""

    x: int
    y: int
    rgb: tuple[int, int, int]
    hue_deg: float
    saturation_pct: float
    value_pct: float


@dataclass(frozen=True, slots=True)
class ColorRegionSample:
    """Summary and suggested thresholds for a rectangular source region."""

    left: int
    top: int
    right: int
    bottom: int
    pixel_count: int
    hue_deg: float
    saturation_pct: float
    value_pct: float
    thresholds: HSVThresholdSet


@dataclass(frozen=True, slots=True)
class ColorMultiSample:
    """Summary and independent HSV ranges for two to four sparse pixels."""

    samples: tuple[ColorSample, ...]
    hue_deg: float
    saturation_pct: float
    value_pct: float
    threshold_ranges: tuple[HSVThresholdSet, ...]

    @property
    def pixel_count(self) -> int:
        return len(self.samples)


def sample_color(rgb: np.ndarray, x: int, y: int) -> ColorSample:
    """Return a validated pixel sample without retaining or mutating the image."""
    height, width = validate_rgb(rgb)
    if isinstance(x, (bool, np.bool_)) or not isinstance(x, (int, np.integer)):
        raise ValidationError("x", "must be an integer pixel coordinate")
    if isinstance(y, (bool, np.bool_)) or not isinstance(y, (int, np.integer)):
        raise ValidationError("y", "must be an integer pixel coordinate")
    x, y = int(x), int(y)
    if not 0 <= x < width:
        raise ValidationError("x", f"must be in 0..{width - 1}")
    if not 0 <= y < height:
        raise ValidationError("y", f"must be in 0..{height - 1}")

    pixel = rgb[y:y + 1, x:x + 1]
    hue, saturation, value = rgb_to_hsv(pixel)[0, 0]
    red, green, blue = (int(channel) for channel in rgb[y, x])
    return ColorSample(
        x=x,
        y=y,
        rgb=(red, green, blue),
        hue_deg=float(hue),
        saturation_pct=float(saturation),
        value_pct=float(value),
    )


def suggest_thresholds(
    sample: ColorSample,
    *,
    hue_tolerance_deg: int = 15,
    saturation_tolerance_pct: int = 15,
    value_tolerance_pct: int = 15,
) -> HSVThresholdSet:
    """Build an inclusive threshold range centered on a sampled color.

    Hue uses a circular interval. For nearly achromatic samples, hue carries
    little useful information, so the complete hue range is suggested.
    """
    for name, value, maximum in (
        ("hue_tolerance_deg", hue_tolerance_deg, 180),
        ("saturation_tolerance_pct", saturation_tolerance_pct, 100),
        ("value_tolerance_pct", value_tolerance_pct, 100),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
            raise ValidationError(name, f"must be an integer in 0..{maximum}")
    components = (sample.hue_deg, sample.saturation_pct, sample.value_pct)
    if not all(math.isfinite(value) for value in components):
        raise ValidationError("sample", "HSV components must be finite")
    if not (
        0.0 <= sample.hue_deg < 360.0
        and 0.0 <= sample.saturation_pct <= 100.0
        and 0.0 <= sample.value_pct <= 100.0
    ):
        raise ValidationError("sample", "HSV components are outside their valid ranges")

    if sample.saturation_pct < 5.0 or hue_tolerance_deg == 180:
        lower_hue, upper_hue = 0, 360
    else:
        lower_hue = math.floor(sample.hue_deg - hue_tolerance_deg) % 360
        upper_hue = math.ceil(sample.hue_deg + hue_tolerance_deg) % 360
    lower_saturation = max(0, math.floor(sample.saturation_pct - saturation_tolerance_pct))
    upper_saturation = min(100, math.ceil(sample.saturation_pct + saturation_tolerance_pct))
    lower_value = max(0, math.floor(sample.value_pct - value_tolerance_pct))
    upper_value = min(100, math.ceil(sample.value_pct + value_tolerance_pct))
    return HSVThresholdSet(
        lower_h_deg=lower_hue,
        upper_h_deg=upper_hue,
        lower_s_pct=lower_saturation,
        upper_s_pct=upper_saturation,
        lower_v_pct=lower_value,
        upper_v_pct=upper_value,
    )


def _validate_tolerance(name: str, value: int, maximum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise ValidationError(name, f"must be an integer in 0..{maximum}")


def _circular_hue_range(hues: np.ndarray, padding: int) -> tuple[int, int]:
    if hues.size == 0:
        return 0, 360
    ordered = np.sort(hues.astype(np.float64, copy=False))
    following = np.roll(ordered, -1)
    gaps = np.mod(following - ordered, 360.0)
    largest_gap_index = int(np.argmax(gaps))
    start = float(following[largest_gap_index])
    end = float(ordered[largest_gap_index])
    arc = (end - start) % 360.0
    if arc + 2 * padding >= 360.0:
        return 0, 360
    lower = math.floor(start - padding) % 360
    upper = math.ceil(start + arc + padding) % 360
    return lower, upper


def sample_colors(
    rgb: np.ndarray,
    coordinates,
    *,
    hue_padding_deg: int = 5,
    saturation_padding_pct: int = 5,
    value_padding_pct: int = 5,
) -> ColorMultiSample:
    """Create one independent HSV range per explicitly selected pixel."""
    validate_rgb(rgb)
    try:
        points = tuple(coordinates)
    except TypeError as error:
        raise ValidationError("coordinates", "must be an iterable of (x, y) pairs") from error
    if not 2 <= len(points) <= 4:
        raise ValidationError("coordinates", "must contain 2..4 pixel positions")
    samples = []
    for index, point in enumerate(points):
        if not isinstance(point, (tuple, list)) or len(point) != 2:
            raise ValidationError(f"coordinates[{index}]", "must be an (x, y) pair")
        samples.append(sample_color(rgb, point[0], point[1]))

    _validate_tolerance("hue_padding_deg", hue_padding_deg, 180)
    _validate_tolerance("saturation_padding_pct", saturation_padding_pct, 100)
    _validate_tolerance("value_padding_pct", value_padding_pct, 100)
    hue = np.array([sample.hue_deg for sample in samples], dtype=np.float64)
    saturation = np.array(
        [sample.saturation_pct for sample in samples], dtype=np.float64
    )
    value = np.array([sample.value_pct for sample in samples], dtype=np.float64)
    chromatic_hue = hue[saturation >= 5.0]
    if chromatic_hue.size:
        angles = np.deg2rad(chromatic_hue)
        representative_hue = math.degrees(
            math.atan2(float(np.sin(angles).mean()), float(np.cos(angles).mean()))
        ) % 360.0
    else:
        representative_hue = 0.0
    threshold_ranges = tuple(
        suggest_thresholds(
            sample,
            hue_tolerance_deg=hue_padding_deg,
            saturation_tolerance_pct=saturation_padding_pct,
            value_tolerance_pct=value_padding_pct,
        )
        for sample in samples
    )
    return ColorMultiSample(
        samples=tuple(samples),
        hue_deg=representative_hue,
        saturation_pct=float(np.median(saturation)),
        value_pct=float(np.median(value)),
        threshold_ranges=threshold_ranges,
    )


def sample_color_region(
    rgb: np.ndarray,
    left: int,
    top: int,
    right: int,
    bottom: int,
    *,
    hue_padding_deg: int = 5,
    saturation_padding_pct: int = 5,
    value_padding_pct: int = 5,
) -> ColorRegionSample:
    """Summarize a nonempty ROI and suggest bounds that include its HSV spread."""
    height, width = validate_rgb(rgb)
    coordinates = {"left": left, "top": top, "right": right, "bottom": bottom}
    for name, value in coordinates.items():
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
            raise ValidationError(name, "must be an integer pixel boundary")
        coordinates[name] = int(value)
    left, top, right, bottom = (
        coordinates["left"], coordinates["top"], coordinates["right"], coordinates["bottom"]
    )
    if not (0 <= left < right <= width):
        raise ValidationError("roi", f"horizontal bounds must satisfy 0 <= left < right <= {width}")
    if not (0 <= top < bottom <= height):
        raise ValidationError("roi", f"vertical bounds must satisfy 0 <= top < bottom <= {height}")
    _validate_tolerance("hue_padding_deg", hue_padding_deg, 180)
    _validate_tolerance("saturation_padding_pct", saturation_padding_pct, 100)
    _validate_tolerance("value_padding_pct", value_padding_pct, 100)

    hsv = rgb_to_hsv(rgb[top:bottom, left:right]).reshape(-1, 3)
    hue, saturation, value = hsv[:, 0], hsv[:, 1], hsv[:, 2]
    chromatic_hue = hue[saturation >= 5.0]
    lower_hue, upper_hue = _circular_hue_range(chromatic_hue, hue_padding_deg)
    if chromatic_hue.size:
        angles = np.deg2rad(chromatic_hue)
        representative_hue = math.degrees(
            math.atan2(float(np.sin(angles).mean()), float(np.cos(angles).mean()))
        ) % 360.0
    else:
        representative_hue = 0.0
    thresholds = HSVThresholdSet(
        lower_h_deg=lower_hue,
        upper_h_deg=upper_hue,
        lower_s_pct=max(0, math.floor(float(saturation.min()) - saturation_padding_pct)),
        upper_s_pct=min(100, math.ceil(float(saturation.max()) + saturation_padding_pct)),
        lower_v_pct=max(0, math.floor(float(value.min()) - value_padding_pct)),
        upper_v_pct=min(100, math.ceil(float(value.max()) + value_padding_pct)),
    )
    return ColorRegionSample(
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        pixel_count=(right - left) * (bottom - top),
        hue_deg=representative_hue,
        saturation_pct=float(np.median(saturation)),
        value_pct=float(np.median(value)),
        thresholds=thresholds,
    )


HSV_PRESETS = MappingProxyType({
    "All colors": HSVThresholdSet(),
    "Red": HSVThresholdSet(350, 10, 50, 100, 20, 100),
    "Yellow": HSVThresholdSet(45, 75, 45, 100, 20, 100),
    "Green": HSVThresholdSet(90, 150, 35, 100, 20, 100),
    "Blue": HSVThresholdSet(200, 260, 35, 100, 20, 100),
})

