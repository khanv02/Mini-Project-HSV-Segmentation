"""Optional marker-controlled separation constrained by the selected mask."""

import cv2
import numpy as np

from ..errors import ValidationError
from ..models import WatershedResult, WatershedSettings, validate_rgb
from .object_analysis import analyze_labels


def _empty(
    shape, status: str, reason: str, *, marker_count: int = 0,
    seed_pixel_count: int = 0,
) -> WatershedResult:
    labels = np.zeros(shape, dtype=np.int32)
    mask = np.zeros(shape, dtype=np.uint8)
    return WatershedResult(
        status,
        labels,
        mask.copy(),
        mask,
        reason,
        analyze_labels(labels),
        marker_count,
        seed_pixel_count,
    )


def _build_markers_with_diagnostics(
    mask: np.ndarray, settings: WatershedSettings
) -> tuple[np.ndarray | None, str | None, int, int]:
    """Build independent local-peak cores and report their observable counts."""
    if (
        not isinstance(mask, np.ndarray)
        or mask.dtype != np.uint8
        or mask.ndim != 2
        or min(mask.shape, default=0) == 0
        or not np.all((mask == 0) | (mask == 255))
    ):
        raise ValidationError("mask", "must be a nonempty binary uint8 array")
    if not isinstance(settings, WatershedSettings):
        raise ValidationError("watershed_settings", "must be WatershedSettings")
    if min(mask.shape) < 3:
        return None, "source dimensions are too small for Watershed markers", 0, 0
    if not np.any(mask):
        return None, "foreground mask is empty", 0, 0

    padded = np.pad(mask, 1, mode="constant")
    distance = cv2.distanceTransform(padded, cv2.DIST_L2, 5)[1:-1, 1:-1]
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (settings.kernel_size, settings.kernel_size)
    )
    local_maximum = (
        (distance > 0)
        & np.isclose(distance, cv2.dilate(distance, kernel), rtol=0.0, atol=1e-5)
    )
    if not np.any(local_maximum):
        return None, "no local distance peaks were found", 0, 0

    # Label the nearest local-maximum plateau for every pixel. This keeps each
    # object's core independent even when a low seed fraction makes cores wide.
    peak_source = np.full(mask.shape, 255, dtype=np.uint8)
    peak_source[local_maximum] = 0
    _, nearest_peak = cv2.distanceTransformWithLabels(
        peak_source,
        cv2.DIST_L2,
        5,
        labelType=cv2.DIST_LABEL_CCOMP,
    )
    peak_ids = np.unique(nearest_peak[local_maximum])
    peak_ids = peak_ids[peak_ids > 0]
    marker_count = int(peak_ids.size)
    if marker_count < 2:
        return (
            None,
            f"only {marker_count} local peak marker was found; at least 2 are required",
            marker_count,
            0,
        )

    peak_heights = np.zeros(int(nearest_peak.max()) + 1, dtype=np.float32)
    np.maximum.at(
        peak_heights,
        nearest_peak[local_maximum],
        distance[local_maximum],
    )
    local_threshold = settings.seed_fraction * peak_heights[nearest_peak]
    seed_pixels = (mask == 255) & (distance > local_threshold)
    seed_pixel_count = int(np.count_nonzero(seed_pixels))

    dilated = (
        cv2.dilate(mask, kernel, iterations=settings.background_iterations)
        if settings.background_iterations
        else mask.copy()
    )
    known_background = dilated == 0
    if not np.any(known_background):
        return (
            None,
            "no known background is available for Watershed",
            marker_count,
            seed_pixel_count,
        )
    markers = np.zeros(mask.shape, dtype=np.int32)
    markers[known_background] = 1
    markers[seed_pixels] = nearest_peak[seed_pixels] + 1
    return markers, None, marker_count, seed_pixel_count


def build_markers(
    mask: np.ndarray, settings: WatershedSettings
) -> tuple[np.ndarray | None, str | None]:
    markers, reason, _marker_count, _seed_pixel_count = (
        _build_markers_with_diagnostics(mask, settings)
    )
    return markers, reason


def separate_watershed(
    rgb: np.ndarray, mask: np.ndarray, settings: WatershedSettings, min_area_px: int = 0
) -> WatershedResult:
    shape = validate_rgb(rgb)
    if not isinstance(mask, np.ndarray) or mask.shape != shape:
        raise ValidationError("mask", "must match RGB dimensions")
    markers, reason, marker_count, seed_pixel_count = _build_markers_with_diagnostics(
        mask, settings
    )
    if reason:
        status = "empty" if not np.any(mask) else "not_applied"
        return _empty(
            shape,
            status,
            reason,
            marker_count=marker_count,
            seed_pixel_count=seed_pixel_count,
        )
    working = cv2.cvtColor(np.ascontiguousarray(rgb), cv2.COLOR_RGB2BGR)
    output = cv2.watershed(working, markers.copy())
    boundaries = (output == -1) & (mask == 255)
    object_labels = np.where(
        (output >= 2) & (mask == 255), output - 1, 0
    ).astype(np.int32)
    analysis = analyze_labels(object_labels, min_area_px)
    ridge_mask = np.where(boundaries, 255, 0).astype(np.uint8)
    return WatershedResult(
        "applied", analysis.labels, ridge_mask, analysis.filtered_mask,
        None, analysis, marker_count, seed_pixel_count,
    )
