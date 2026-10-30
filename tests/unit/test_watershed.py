import numpy as np

from hsv_segmentation.models import WatershedSettings
from hsv_segmentation.processing.watershed import (
    MAX_MEANINGFUL_MARKERS,
    MAX_PREFLIGHT_MARKERS,
    MAX_WATERSHED_MARKERS,
    _select_prominent_peaks,
    build_markers,
    separate_watershed,
)
from tests.fixtures.analysis_cases import touching_disks


def test_touching_disks_produce_two_separated_labels() -> None:
    rgb, mask = touching_disks()
    result = separate_watershed(rgb, mask, WatershedSettings(True, 0.7, 1, 3))
    assert result.status == "applied"
    assert result.analysis.retained_count == 2
    assert np.all(result.foreground_mask[mask == 0] == 0)
    assert np.all(result.boundaries[mask == 0] == 0)


def test_empty_and_insufficient_markers_are_truthful() -> None:
    rgb = np.zeros((20, 20, 3), np.uint8); empty = np.zeros((20, 20), np.uint8)
    assert separate_watershed(rgb, empty, WatershedSettings(True)).status == "empty"
    one = empty.copy(); one[5:15, 5:15] = 255
    result = separate_watershed(rgb, one, WatershedSettings(True))
    assert result.status == "not_applied" and "only 1 local peak" in result.reason
    assert result.marker_count == 1


def test_markers_reserve_background_and_two_foregrounds() -> None:
    _, mask = touching_disks()
    markers, reason = build_markers(mask, WatershedSettings(True, 0.7))
    assert reason is None and 1 in markers
    assert len([v for v in np.unique(markers) if v >= 2]) == 2


def test_seed_fraction_resizes_local_cores_without_losing_markers() -> None:
    rgb, mask = touching_disks()

    wide = separate_watershed(rgb, mask, WatershedSettings(True, 0.3))
    narrow = separate_watershed(rgb, mask, WatershedSettings(True, 0.9))

    assert wide.status == narrow.status == "applied"
    assert wide.marker_count == narrow.marker_count == 2
    assert wide.analysis.retained_count == narrow.analysis.retained_count == 2
    assert wide.seed_pixel_count > narrow.seed_pixel_count


def test_local_peaks_preserve_small_object_at_high_seed_fraction() -> None:
    size = 120
    y, x = np.ogrid[:size, :size]
    large = (x - 40) ** 2 + (y - 60) ** 2 <= 30 ** 2
    small = (x - 82) ** 2 + (y - 60) ** 2 <= 16 ** 2
    mask = np.where(large | small, 255, 0).astype(np.uint8)
    rgb = np.zeros((size, size, 3), dtype=np.uint8)
    rgb[mask == 255] = (220, 70, 40)

    result = separate_watershed(rgb, mask, WatershedSettings(True, 0.9))

    assert result.status == "applied"
    assert result.marker_count == result.analysis.retained_count == 2


def test_high_detail_mask_stops_before_expensive_separation() -> None:
    size = 384
    y, x = np.ogrid[:size, :size]
    mask = np.where((x % 4 == 1) & (y % 4 == 1), 255, 0).astype(np.uint8)
    rgb = np.zeros((size, size, 3), dtype=np.uint8)

    result = separate_watershed(rgb, mask, WatershedSettings(True))

    assert result.status == "not_applied"
    assert result.marker_count > MAX_WATERSHED_MARKERS
    assert result.seed_pixel_count == 0
    assert "too detailed for safe separation" in result.reason
    assert "morphology" in result.reason
    assert not np.any(result.foreground_mask)


def test_large_detailed_mask_is_rejected_by_fast_preflight() -> None:
    size = 1100
    y, x = np.ogrid[:size, :size]
    mask = np.where((x % 4 == 1) & (y % 4 == 1), 255, 0).astype(np.uint8)
    rgb = np.zeros((size, size, 3), dtype=np.uint8)

    result = separate_watershed(rgb, mask, WatershedSettings(True))

    assert result.status == "not_applied"
    assert result.marker_count > MAX_PREFLIGHT_MARKERS
    assert "during preflight" in result.reason
    assert result.analysis is None


def test_nearby_distance_peaks_are_merged_before_marker_creation() -> None:
    mask = np.full((80, 100), 255, dtype=np.uint8)
    distance = np.zeros(mask.shape, dtype=np.float32)
    local_maximum = np.zeros(mask.shape, dtype=bool)
    for x, height in ((40, 10.0), (45, 9.0), (75, 8.0)):
        distance[40, x] = height
        local_maximum[40, x] = True

    selected, raw_count = _select_prominent_peaks(mask, distance, local_maximum)

    assert raw_count == 3
    assert np.count_nonzero(selected) == 2
    assert selected[40, 40]
    assert not selected[40, 45]
    assert selected[40, 75]


def test_too_many_surviving_regions_are_rejected_as_oversegmentation() -> None:
    size = 180
    y, x = np.ogrid[:size, :size]
    foreground = np.zeros((size, size), dtype=bool)
    for center_y in (20, 55, 90, 125, 160):
        for center_x in (20, 65, 110, 155):
            foreground |= (x - center_x) ** 2 + (y - center_y) ** 2 <= 6 ** 2
    mask = np.where(foreground, 255, 0).astype(np.uint8)
    rgb = np.zeros((size, size, 3), dtype=np.uint8)

    result = separate_watershed(rgb, mask, WatershedSettings(True))

    assert result.status == "not_applied"
    assert result.marker_count > MAX_MEANINGFUL_MARKERS
    assert "unreadable over-segmented result" in result.reason
