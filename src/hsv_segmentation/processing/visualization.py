"""Pure display-only compositions derived from validated segmentation data."""

from numbers import Real

import numpy as np

from ..errors import ValidationError
from ..models import validate_rgb


def compose_segmentation_overlay(
    rgb: np.ndarray,
    mask: np.ndarray,
    *,
    color: tuple[int, int, int] = (0, 255, 80),
    opacity: float = 0.35,
) -> np.ndarray:
    """Tint selected pixels while retaining the complete original image."""
    height, width = validate_rgb(rgb)
    if (
        not isinstance(mask, np.ndarray)
        or mask.dtype != np.uint8
        or mask.shape != (height, width)
        or not np.all((mask == 0) | (mask == 255))
    ):
        raise ValidationError("mask", "must be a source-sized binary uint8 array")
    if (
        not isinstance(color, tuple)
        or len(color) != 3
        or any(isinstance(channel, bool) or not isinstance(channel, int) or not 0 <= channel <= 255
               for channel in color)
    ):
        raise ValidationError("color", "must contain three integer channels in 0..255")
    if isinstance(opacity, bool) or not isinstance(opacity, Real) or not 0.0 <= opacity <= 1.0:
        raise ValidationError("opacity", "must be a number in 0..1")

    overlay = rgb.copy()
    selected = mask == 255
    tint = np.asarray(color, dtype=np.float64)
    blended = np.rint(
        rgb[selected].astype(np.float64) * (1.0 - float(opacity))
        + tint * float(opacity)
    )
    overlay[selected] = blended.astype(np.uint8)
    return overlay

