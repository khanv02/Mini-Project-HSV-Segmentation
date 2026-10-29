"""Pure exact-grayscale segmentation and deterministic global Otsu thresholding."""

from numbers import Integral

import numpy as np

from ..errors import ValidationError
from ..models import GrayscaleEligibility, OtsuOutcome, validate_rgb


def classify_grayscale(
    rgb: np.ndarray, source_sha256: str, frame_index: int | None = None
) -> GrayscaleEligibility:
    """Return eligibility using exact equality of all displayed RGB channels."""
    validate_rgb(rgb)
    eligible = bool(np.all(rgb[..., 0] == rgb[..., 1]) and np.all(rgb[..., 1] == rgb[..., 2]))
    return GrayscaleEligibility(
        eligible=eligible,
        source_sha256=source_sha256,
        frame_index=frame_index,
        reason=None if eligible else "RGB channels are not equal at every pixel.",
    )


def extract_intensity(rgb: np.ndarray) -> np.ndarray:
    """Return owned uint8 intensity pixels from an exactly grayscale RGB image."""
    validate_rgb(rgb)
    if not (np.all(rgb[..., 0] == rgb[..., 1]) and np.all(rgb[..., 1] == rgb[..., 2])):
        raise ValidationError("rgb", "must have equal RGB channels at every pixel")
    return rgb[..., 0].copy()


def generate_grayscale_mask(
    intensity: np.ndarray, threshold: int, polarity: str
) -> np.ndarray:
    """Select `I > T` for bright or the exact complement `I <= T` for dark."""
    if (not isinstance(intensity, np.ndarray) or intensity.dtype != np.uint8
            or intensity.ndim != 2 or min(intensity.shape, default=0) == 0):
        raise ValidationError("intensity", "must be a nonempty two-dimensional uint8 array")
    if isinstance(threshold, (bool, np.bool_)) or not isinstance(threshold, Integral):
        raise ValidationError("threshold", "must be an integer in 0..255")
    threshold = int(threshold)
    if not 0 <= threshold <= 255:
        raise ValidationError("threshold", "must be an integer in 0..255")
    if polarity == "bright":
        selected = intensity > threshold
    elif polarity == "dark":
        selected = intensity <= threshold
    else:
        raise ValidationError("polarity", "must be bright or dark")
    return np.where(selected, 255, 0).astype(np.uint8)


def compute_otsu_threshold(
    intensity: np.ndarray, source_sha256: str, frame_index: int | None = None
) -> OtsuOutcome:
    """Maximize between-class variance and choose the smallest optimal threshold."""
    if (not isinstance(intensity, np.ndarray) or intensity.dtype != np.uint8
            or intensity.ndim != 2 or min(intensity.shape, default=0) == 0):
        raise ValidationError("intensity", "must be a nonempty two-dimensional uint8 array")
    histogram = np.bincount(intensity.ravel(), minlength=256).astype(np.int64)
    total = int(histogram.sum())
    cumulative_count = np.cumsum(histogram)[:-1]
    cumulative_sum = np.cumsum(histogram * np.arange(256, dtype=np.int64))[:-1]
    total_sum = int(cumulative_sum[-1] + histogram[-1] * 255)
    valid = (cumulative_count > 0) & (cumulative_count < total)
    if not np.any(valid):
        return OtsuOutcome(
            status="unavailable", source_sha256=source_sha256, frame_index=frame_index,
            reason="No meaningful split exists because the image has one intensity class.",
        )
    weight0 = cumulative_count[valid].astype(np.float64)
    weight1 = total - weight0
    mean0 = cumulative_sum[valid] / weight0
    mean1 = (total_sum - cumulative_sum[valid]) / weight1
    variance = weight0 * weight1 * (mean0 - mean1) ** 2
    candidates = np.nonzero(valid)[0]
    threshold = int(candidates[int(np.argmax(variance))])
    return OtsuOutcome(
        status="applied", threshold=threshold, source_sha256=source_sha256,
        frame_index=frame_index,
    )
