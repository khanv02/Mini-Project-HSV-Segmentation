import numpy as np

from hsv_segmentation.models import WatershedSettings
from hsv_segmentation.processing.watershed import build_markers, separate_watershed
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
