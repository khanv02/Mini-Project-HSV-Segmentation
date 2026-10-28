"""Connected-region measurements derived from binary HSV masks or label maps."""

import cv2
import numpy as np

from ..errors import ValidationError
from ..models import AnalysisSettings, RegionAnalysis, RegionStatistics


def _validate_mask(mask: np.ndarray) -> None:
    if (
        not isinstance(mask, np.ndarray) or mask.dtype != np.uint8 or mask.ndim != 2
        or min(mask.shape, default=0) == 0
        or not np.all((mask == 0) | (mask == 255))
    ):
        raise ValidationError("mask", "must be a nonempty binary uint8 array")


def _normalize_labels(labels: np.ndarray, min_area_px: int) -> RegionAnalysis:
    if (
        not isinstance(labels, np.ndarray) or labels.dtype != np.int32 or labels.ndim != 2
        or min(labels.shape, default=0) == 0 or np.any(labels < 0)
    ):
        raise ValidationError("labels", "must be a nonempty nonnegative int32 array")
    if isinstance(min_area_px, bool) or not isinstance(min_area_px, (int, np.integer)) or min_area_px < 0:
        raise ValidationError("min_area_px", "must be a nonnegative integer")
    flat = labels.ravel()
    values, first_indices, counts = np.unique(
        flat, return_index=True, return_counts=True
    )
    foreground = values > 0
    present = values[foreground].astype(np.int32, copy=False)
    first_indices = first_indices[foreground]
    counts = counts[foreground]
    raw_count = int(present.size)

    ys, xs = np.nonzero(labels)
    compact = np.searchsorted(present, labels[ys, xs])
    x_min = np.full(raw_count, labels.shape[1], dtype=np.int64)
    y_min = np.full(raw_count, labels.shape[0], dtype=np.int64)
    x_max = np.full(raw_count, -1, dtype=np.int64)
    y_max = np.full(raw_count, -1, dtype=np.int64)
    np.minimum.at(x_min, compact, xs)
    np.minimum.at(y_min, compact, ys)
    np.maximum.at(x_max, compact, xs)
    np.maximum.at(y_max, compact, ys)
    x_sum = np.bincount(compact, weights=xs, minlength=raw_count)
    y_sum = np.bincount(compact, weights=ys, minlength=raw_count)

    retained = np.flatnonzero(counts >= int(min_area_px))
    retained = retained[np.argsort(first_indices[retained], kind="stable")]
    new_ids = np.zeros(raw_count, dtype=np.int32)
    new_ids[retained] = np.arange(1, retained.size + 1, dtype=np.int32)
    normalized = np.zeros(labels.shape, dtype=np.int32)
    normalized[ys, xs] = new_ids[compact]
    regions = []
    for new_id, index in enumerate(retained, 1):
        old_id = int(present[index])
        x0, y0 = int(x_min[index]), int(y_min[index])
        width = int(x_max[index] - x_min[index] + 1)
        height = int(y_max[index] - y_min[index] + 1)
        selected = labels[y0:y0 + height, x0:x0 + width] == old_id
        binary = np.where(selected, 255, 0).astype(np.uint8)
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        offset = np.asarray([[[x0, y0]]], dtype=np.int32)
        regions.append(RegionStatistics(
            new_id, int(counts[index]),
            float(x_sum[index] / counts[index]), float(y_sum[index] / counts[index]),
            (int(x0), int(y0), int(width), int(height)),
            tuple(np.asarray(c, dtype=np.int32) + offset for c in contours),
        ))
    filtered = np.where(normalized > 0, 255, 0).astype(np.uint8)
    return RegionAnalysis(normalized, filtered, raw_count, tuple(regions))


def analyze_components(mask: np.ndarray, settings: AnalysisSettings) -> RegionAnalysis:
    """Measure connected foreground using explicit 4- or 8-neighbor connectivity."""
    _validate_mask(mask)
    if not isinstance(settings, AnalysisSettings):
        raise ValidationError("analysis_settings", "must be AnalysisSettings")
    _, labels, _, _ = cv2.connectedComponentsWithStats(
        mask, connectivity=settings.connectivity, ltype=cv2.CV_32S
    )
    return _normalize_labels(labels.astype(np.int32, copy=False), settings.min_area_px)


def analyze_labels(labels: np.ndarray, min_area_px: int = 0) -> RegionAnalysis:
    """Measure already-separated positive labels without reconnecting their union."""
    return _normalize_labels(labels, min_area_px)
