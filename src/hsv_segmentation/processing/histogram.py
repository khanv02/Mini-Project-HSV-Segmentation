"""Pure HSV distribution counting for one accepted source or frame."""

import numpy as np

from ..models import HSVHistogram
from .segmentation import validate_hsv


HUE_SATURATION_CUTOFF_PCT = 5.0


def compute_hsv_histogram(hsv: np.ndarray) -> HSVHistogram:
    """Return exact one-unit HSV bins without mutating the source array."""
    validate_hsv(hsv)
    hue = hsv[..., 0].reshape(-1)
    saturation = hsv[..., 1].reshape(-1)
    value = hsv[..., 2].reshape(-1)

    hue_included = saturation >= HUE_SATURATION_CUTOFF_PCT
    hue_bins = np.floor(hue[hue_included]).astype(np.int64)
    saturation_bins = np.minimum(np.floor(saturation), 100).astype(np.int64)
    value_bins = np.minimum(np.floor(value), 100).astype(np.int64)

    return HSVHistogram(
        hue_counts=np.bincount(hue_bins, minlength=360).astype(np.int64),
        saturation_counts=np.bincount(
            saturation_bins, minlength=101
        ).astype(np.int64),
        value_counts=np.bincount(value_bins, minlength=101).astype(np.int64),
        excluded_hue_count=int((~hue_included).sum()),
    )
