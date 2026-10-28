import numpy as np
import pytest

from hsv_segmentation.errors import ValidationError
from hsv_segmentation.models import AnalysisSettings
from hsv_segmentation.processing.object_analysis import analyze_components, analyze_labels
from tests.fixtures.analysis_cases import diagonal_pixels, rectangles_with_noise


def test_exact_statistics_and_inclusive_minimum_area() -> None:
    mask = rectangles_with_noise()
    result = analyze_components(mask, AnalysisSettings(True, 8, 4))
    assert result.raw_count == 3
    assert [r.area_px for r in result.regions] == [4, 9]
    assert [r.box for r in result.regions] == [(1, 1, 2, 2), (7, 5, 3, 3)]
    assert [(r.centroid_x, r.centroid_y) for r in result.regions] == [(1.5, 1.5), (8.0, 6.0)]
    assert np.count_nonzero(result.filtered_mask) == 13


def test_connectivity_changes_diagonal_grouping() -> None:
    mask = diagonal_pixels()
    assert analyze_components(mask, AnalysisSettings(True, 4)).raw_count == 2
    assert analyze_components(mask, AnalysisSettings(True, 8)).raw_count == 1


def test_empty_holed_and_labeled_regions() -> None:
    assert analyze_components(np.zeros((4, 4), np.uint8), AnalysisSettings(True)).raw_count == 0
    mask = np.full((5, 5), 255, np.uint8); mask[2, 2] = 0
    assert analyze_components(mask, AnalysisSettings(True)).regions[0].area_px == 24
    labels = np.array([[1, 2], [1, 2]], dtype=np.int32)
    assert [r.area_px for r in analyze_labels(labels).regions] == [2, 2]


@pytest.mark.parametrize("bad", [np.zeros((2, 2), bool), np.zeros((0, 2), np.uint8)])
def test_rejects_invalid_masks(bad) -> None:
    with pytest.raises(ValidationError):
        analyze_components(bad, AnalysisSettings(True))
