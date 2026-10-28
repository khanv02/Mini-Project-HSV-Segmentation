"""Optional marker-controlled separation constrained by the HSV-derived mask."""

import cv2
import numpy as np

from ..errors import ValidationError
from ..models import WatershedResult, WatershedSettings, validate_rgb
from .object_analysis import analyze_labels


def _empty(shape, status: str, reason: str) -> WatershedResult:
    labels = np.zeros(shape, dtype=np.int32)
    mask = np.zeros(shape, dtype=np.uint8)
    return WatershedResult(status, labels, mask.copy(), mask, reason, analyze_labels(labels))


def build_markers(mask: np.ndarray, settings: WatershedSettings) -> tuple[np.ndarray | None, str | None]:
    if (
        not isinstance(mask, np.ndarray) or mask.dtype != np.uint8 or mask.ndim != 2
        or min(mask.shape, default=0) == 0
        or not np.all((mask == 0) | (mask == 255))
    ):
        raise ValidationError("mask", "must be a nonempty binary uint8 array")
    if not isinstance(settings, WatershedSettings):
        raise ValidationError("watershed_settings", "must be WatershedSettings")
    if min(mask.shape) < 3:
        return None, "source dimensions are too small for Watershed markers"
    if not np.any(mask):
        return None, "HSV foreground is empty"
    padded = np.pad(mask, 1, mode="constant")
    distance = cv2.distanceTransform(padded, cv2.DIST_L2, 5)[1:-1, 1:-1]
    maximum = float(distance.max())
    seeds = np.where(distance > settings.seed_fraction * maximum, 255, 0).astype(np.uint8)
    count, seed_labels = cv2.connectedComponents(seeds, connectivity=8, ltype=cv2.CV_32S)
    if count - 1 < 2:
        return None, "fewer than two foreground marker regions were found"
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (settings.kernel_size, settings.kernel_size)
    )
    if settings.background_iterations:
        dilated = cv2.dilate(mask, kernel, iterations=settings.background_iterations)
    else:
        dilated = mask.copy()
    known_background = dilated == 0
    if not np.any(known_background):
        return None, "no known background is available for Watershed"
    markers = np.zeros(mask.shape, dtype=np.int32)
    markers[known_background] = 1
    markers[seed_labels > 0] = seed_labels[seed_labels > 0] + 1
    return markers, None


def separate_watershed(
    rgb: np.ndarray, mask: np.ndarray, settings: WatershedSettings, min_area_px: int = 0
) -> WatershedResult:
    shape = validate_rgb(rgb)
    if not isinstance(mask, np.ndarray) or mask.shape != shape:
        raise ValidationError("mask", "must match RGB dimensions")
    markers, reason = build_markers(mask, settings)
    if reason:
        status = "empty" if not np.any(mask) else "not_applied"
        return _empty(shape, status, reason)
    working = cv2.cvtColor(np.ascontiguousarray(rgb), cv2.COLOR_RGB2BGR)
    output = cv2.watershed(working, markers.copy())
    boundaries = (output == -1) & (mask == 255)
    object_labels = np.where((output >= 2) & (mask == 255), output - 1, 0).astype(np.int32)
    analysis = analyze_labels(object_labels, min_area_px)
    ridge_mask = np.where(boundaries, 255, 0).astype(np.uint8)
    return WatershedResult(
        "applied", analysis.labels, ridge_mask, analysis.filtered_mask,
        None, analysis,
    )
