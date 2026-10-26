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

    # An odd square kernel gives a centered, symmetric neighborhood. Sizes
    # are deliberately bounded in MorphologySettings to avoid over-cleaning.
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (settings.kernel_size, settings.kernel_size)
    )
    operations = {
        "opening": (cv2.MORPH_OPEN,),
        "closing": (cv2.MORPH_CLOSE,),
        "opening_closing": (cv2.MORPH_OPEN, cv2.MORPH_CLOSE),
    }[settings.operation]
    result = mask
    for operation in operations:
        # OpenCV's morphologyDefaultBorderValue is operation-aware: it avoids
        # treating pixels outside the image as background during erosion.
        result = cv2.morphologyEx(result, operation, kernel)
    return result.copy()

