"""Optional marker-controlled separation constrained by the selected mask."""

import cv2
import numpy as np

from ..errors import ValidationError
from ..models import WatershedResult, WatershedSettings, validate_rgb
from .object_analysis import analyze_labels


# Object analysis retains contours and statistics for every separated label. A
# highly textured/noisy mask can contain tens of thousands of local peaks, for
# which Watershed is both semantically unhelpful and expensive enough to exhaust
# desktop memory. Keep the optional extension bounded and fall back to the
# baseline mask with an actionable status instead.
MAX_WATERSHED_MARKERS = 2048
MAX_MEANINGFUL_MARKERS = 16
PREFLIGHT_MIN_PIXELS = 1_000_000
PREFLIGHT_TILE_SIZE = 256
MAX_PREFLIGHT_MARKERS = 512
Peak = tuple[float, int, int, int]  # height, y, x, connected-component ID


def _distance_peaks(
    mask: np.ndarray, kernel: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return the padded L2 distance map and its local-maximum pixels."""
    padded = np.pad(mask, 1, mode="constant")
    distance = cv2.distanceTransform(padded, cv2.DIST_L2, 5)[1:-1, 1:-1]
    local_maximum = (
        (distance > 0)
        & np.isclose(distance, cv2.dilate(distance, kernel), rtol=0.0, atol=1e-5)
    )
    return distance, local_maximum


def _extract_peak_candidates(
    mask: np.ndarray,
    distance: np.ndarray,
    plateau_labels: np.ndarray,
    stats: np.ndarray,
    plateau_count: int,
) -> tuple[list[Peak], np.ndarray]:
    """Represent every maximum plateau by its strongest pixel and mask island."""
    component_count, component_labels = cv2.connectedComponents(
        mask, connectivity=8, ltype=cv2.CV_32S
    )
    candidates: list[Peak] = []
    component_maximum = np.zeros(component_count, dtype=np.float32)
    for plateau_id in range(1, plateau_count):
        x0, y0, width, height = stats[plateau_id, :4]
        plateau = plateau_labels[y0:y0 + height, x0:x0 + width] == plateau_id
        values = np.where(
            plateau, distance[y0:y0 + height, x0:x0 + width], -1.0
        )
        local_y, local_x = np.unravel_index(int(np.argmax(values)), values.shape)
        y, x = y0 + int(local_y), x0 + int(local_x)
        peak_height = float(distance[y, x])
        component_id = int(component_labels[y, x])
        candidates.append((peak_height, y, x, component_id))
        component_maximum[component_id] = max(
            component_maximum[component_id], peak_height
        )
    return candidates, component_maximum


def _filter_shallow_peaks(
    candidates: list[Peak], component_maximum: np.ndarray,
) -> list[Peak]:
    """Discard edge noise while preserving the best peak of every mask island."""
    prominent = []
    for candidate in candidates:
        peak_height, _y, _x, component_id = candidate
        strongest = float(component_maximum[component_id])
        minimum_height = min(strongest, max(1.5, strongest * 0.10))
        if peak_height + 1e-5 >= minimum_height:
            prominent.append(candidate)
    return prominent


def _suppress_nearby_peaks(candidates: list[Peak]) -> list[Peak]:
    """Keep at most one peak per local object-radius neighborhood."""
    accepted: list[Peak] = []
    for candidate in sorted(candidates, reverse=True):
        peak_height, y, x, component_id = candidate
        for other_height, other_y, other_x, other_component in accepted:
            if component_id != other_component:
                continue
            radius = max(peak_height, other_height)
            if (x - other_x) ** 2 + (y - other_y) ** 2 < radius ** 2:
                break
        else:
            accepted.append(candidate)
    return accepted


def _select_prominent_peaks(
    mask: np.ndarray, distance: np.ndarray, local_maximum: np.ndarray,
) -> tuple[np.ndarray, int]:
    """Merge nearby/noisy maxima while retaining peaks of distinct mask islands."""
    count, plateau_labels, stats, _centroids = cv2.connectedComponentsWithStats(
        local_maximum.astype(np.uint8), connectivity=8, ltype=cv2.CV_32S
    )
    raw_count = int(count - 1)
    if raw_count == 0 or raw_count > MAX_WATERSHED_MARKERS:
        return np.zeros(mask.shape, dtype=bool), raw_count

    candidates, component_maximum = _extract_peak_candidates(
        mask, distance, plateau_labels, stats, count
    )
    prominent = _filter_shallow_peaks(candidates, component_maximum)
    accepted = _suppress_nearby_peaks(prominent)

    selected = np.zeros(mask.shape, dtype=bool)
    for _height, y, x, _component_id in accepted:
        selected[y, x] = True
    return selected, raw_count


def _count_local_peaks(mask: np.ndarray, kernel: np.ndarray) -> int:
    """Count distance peaks in one mask without retaining the label image."""
    _distance, local_maximum = _distance_peaks(mask, kernel)
    if not np.any(local_maximum):
        return 0
    count, labels = cv2.connectedComponents(
        local_maximum.astype(np.uint8), connectivity=8, ltype=cv2.CV_32S
    )
    del labels
    return int(count - 1)


def _preflight_marker_count(mask: np.ndarray, kernel: np.ndarray) -> int:
    """Sample native-resolution tiles so detailed large masks fail quickly."""
    if mask.size <= PREFLIGHT_MIN_PIXELS:
        return 0
    height, width = mask.shape
    tile_height = min(height, PREFLIGHT_TILE_SIZE)
    tile_width = min(width, PREFLIGHT_TILE_SIZE)
    y_starts = sorted({0, (height - tile_height) // 2, height - tile_height})
    x_starts = sorted({0, (width - tile_width) // 2, width - tile_width})
    marker_count = 0
    for y0 in y_starts:
        for x0 in x_starts:
            tile = mask[y0:y0 + tile_height, x0:x0 + tile_width]
            marker_count += _count_local_peaks(tile, kernel)
            if marker_count > MAX_PREFLIGHT_MARKERS:
                return marker_count
    return marker_count


def _empty(
    shape, status: str, reason: str, *, marker_count: int = 0,
    seed_pixel_count: int = 0,
) -> WatershedResult:
    labels = np.zeros(shape, dtype=np.int32)
    mask = np.zeros(shape, dtype=np.uint8)
    return WatershedResult(
        status,
        labels,
        mask,
        mask,
        reason,
        None,
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

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (settings.kernel_size, settings.kernel_size)
    )
    preflight_count = _preflight_marker_count(mask, kernel)
    if preflight_count > MAX_PREFLIGHT_MARKERS:
        return (
            None,
            f"mask is too detailed for interactive separation (more than "
            f"{MAX_PREFLIGHT_MARKERS} local peaks found during preflight); "
            "reduce noise with morphology or tighten the segmentation",
            preflight_count,
            0,
        )

    distance, local_maximum = _distance_peaks(mask, kernel)
    if not np.any(local_maximum):
        return None, "no local distance peaks were found", 0, 0

    selected_peaks, raw_marker_count = _select_prominent_peaks(
        mask, distance, local_maximum
    )
    if raw_marker_count > MAX_WATERSHED_MARKERS:
        return (
            None,
            f"mask is too detailed for safe separation ({raw_marker_count} markers; "
            f"limit {MAX_WATERSHED_MARKERS}); reduce noise with morphology or "
            "tighten the segmentation",
            raw_marker_count,
            0,
        )
    marker_count = int(np.count_nonzero(selected_peaks))
    if marker_count > MAX_MEANINGFUL_MARKERS:
        return (
            None,
            f"separation would create {marker_count} regions; limit "
            f"{MAX_MEANINGFUL_MARKERS} prevents an unreadable over-segmented result",
            marker_count,
            0,
        )

    # Label the nearest local-maximum plateau for every pixel. This keeps each
    # object's core independent even when a low seed fraction makes cores wide.
    peak_source = np.full(mask.shape, 255, dtype=np.uint8)
    peak_source[selected_peaks] = 0
    _, nearest_peak = cv2.distanceTransformWithLabels(
        peak_source,
        cv2.DIST_L2,
        5,
        labelType=cv2.DIST_LABEL_CCOMP,
    )
    peak_ids = np.unique(nearest_peak[selected_peaks])
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
        nearest_peak[selected_peaks],
        distance[selected_peaks],
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
