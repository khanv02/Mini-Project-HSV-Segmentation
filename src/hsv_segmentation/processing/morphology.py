"""Optional OpenCV morphology for validated binary HSV masks."""

import cv2
import numpy as np

from ..errors import ValidationError
from ..models import MorphologySettings


def _validate_mask(mask: np.ndarray) -> None:
    if (
        not isinstance(mask, np.ndarray)
        or mask.dtype != np.uint8
        or mask.ndim != 2
        or min(mask.shape, default=0) == 0
        or not np.all((mask == 0) | (mask == 255))
    ):
        raise ValidationError(
            "mask", "must be a nonempty binary uint8 array containing only 0 and 255"
        )


def apply_morphology(mask: np.ndarray, settings: MorphologySettings) -> np.ndarray:
    """Return an owned final mask after the configured Opening/Closing operations."""
    _validate_mask(mask)
    if not isinstance(settings, MorphologySettings):
        raise ValidationError("morphology", "must be MorphologySettings")
    if not settings.enabled:
        return mask.copy()

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (settings.kernel_size, settings.kernel_size)
    )
    result = mask
    if settings.operation in {"opening", "opening_closing"}:
        result = cv2.morphologyEx(
            result, cv2.MORPH_OPEN, kernel,
            borderType=cv2.BORDER_CONSTANT, borderValue=0,
        )
    if settings.operation in {"closing", "opening_closing"}:
        result = cv2.morphologyEx(
            result, cv2.MORPH_CLOSE, kernel,
            borderType=cv2.BORDER_CONSTANT, borderValue=0,
        )
    return np.asarray(result, dtype=np.uint8).copy()

