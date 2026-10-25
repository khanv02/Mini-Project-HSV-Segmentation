"""Pure HSV membership and RGB extraction operations."""

from collections.abc import Mapping

import numpy as np

from ..errors import ValidationError
from ..models import HSVThresholdSet, MAX_IMAGE_PIXELS, validate_rgb
from .color import rgb_to_hsv
from .thresholds import validate_thresholds


def validate_hsv(hsv: np.ndarray) -> tuple[int, int]:
    """Validate the shared float64 HSV array contract."""
    if not isinstance(hsv, np.ndarray) or hsv.dtype != np.float64:
        raise ValidationError("hsv", "must be a float64 NumPy array")
    if hsv.ndim != 3 or hsv.shape[2] != 3 or min(hsv.shape[:2]) == 0:
        raise ValidationError("hsv", "must have nonempty shape (height, width, 3)")
    height, width = hsv.shape[:2]
    if height * width > MAX_IMAGE_PIXELS:
        raise ValidationError("hsv", f"exceeds the {MAX_IMAGE_PIXELS:,}-pixel limit")
    if not np.all(np.isfinite(hsv)):
        raise ValidationError("hsv", "must contain only finite values")
    hue = hsv[..., 0]
    saturation = hsv[..., 1]
    value = hsv[..., 2]
    if np.any((hue < 0.0) | (hue >= 360.0)):
        raise ValidationError("hsv", "hue must be in [0, 360)")
    if np.any((saturation < 0.0) | (saturation > 100.0)):
        raise ValidationError("hsv", "saturation must be in [0, 100]")
    if np.any((value < 0.0) | (value > 100.0)):
        raise ValidationError("hsv", "value must be in [0, 100]")
    return height, width


def generate_mask(
    hsv: np.ndarray,
    thresholds: HSVThresholdSet | Mapping[str, object],
) -> np.ndarray:
    """Select pixels in all three inclusive intervals as a 0/255 mask."""
    validate_hsv(hsv)
    bounds = validate_thresholds(thresholds)
    hue = hsv[..., 0]
    saturation = hsv[..., 1]
    value = hsv[..., 2]

    if bounds.wraps_hue:
        hue_selected = (hue >= bounds.lower_h_deg) | (hue <= bounds.upper_h_deg)
    else:
        hue_selected = (hue >= bounds.lower_h_deg) & (hue <= bounds.upper_h_deg)
    selected = (
        hue_selected
        & (saturation >= bounds.lower_s_pct)
        & (saturation <= bounds.upper_s_pct)
        & (value >= bounds.lower_v_pct)
        & (value <= bounds.upper_v_pct)
    )
    return np.where(selected, 255, 0).astype(np.uint8)


def apply_mask(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Return source RGB at selected pixels and black everywhere else."""
    height, width = validate_rgb(rgb)
    if not isinstance(mask, np.ndarray) or mask.dtype != np.uint8:
        raise ValidationError("mask", "must be a uint8 NumPy array")
    if mask.shape != (height, width):
        raise ValidationError("mask", "must match the RGB height and width")
    if not np.all((mask == 0) | (mask == 255)):
        raise ValidationError("mask", "must contain only 0 and 255")
    return np.where((mask == 255)[..., None], rgb, 0).astype(np.uint8)


def segment(
    rgb: np.ndarray,
    thresholds: HSVThresholdSet | Mapping[str, object],
) -> tuple[np.ndarray, np.ndarray]:
    """Convert, select, and extract an RGB image without mutating inputs."""
    validated = validate_thresholds(thresholds)
    mask = generate_mask(rgb_to_hsv(rgb), validated)
    return mask, apply_mask(rgb, mask)
