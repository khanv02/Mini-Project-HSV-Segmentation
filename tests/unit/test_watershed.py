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
    assert result.status == "not_applied" and "fewer than two" in result.reason


def test_markers_reserve_background_and_two_foregrounds() -> None:
    _, mask = touching_disks()
    markers, reason = build_markers(mask, WatershedSettings(True, 0.7))
    assert reason is None and 1 in markers
    assert len([v for v in np.unique(markers) if v >= 2]) == 2
