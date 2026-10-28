"""Display-only segmentation overlay tests."""

import numpy as np
import pytest

from hsv_segmentation.errors import ValidationError
from hsv_segmentation.models import AnalysisSettings, WatershedSettings
from hsv_segmentation.processing.object_analysis import analyze_components
from hsv_segmentation.processing.watershed import separate_watershed
from hsv_segmentation.processing.visualization import (
    compose_confusion_overlay,
    compose_region_annotations,
    compose_segmentation_overlay,
    compose_watershed_overlay,
)
from tests.fixtures.analysis_cases import touching_disks


def test_overlay_tints_only_selected_pixels_without_mutating_inputs() -> None:
    rgb = np.array([[[100, 50, 0], [10, 20, 30]]], dtype=np.uint8)
    mask = np.array([[255, 0]], dtype=np.uint8)
    before_rgb, before_mask = rgb.copy(), mask.copy()

    overlay = compose_segmentation_overlay(rgb, mask, color=(0, 250, 100), opacity=0.5)

    np.testing.assert_array_equal(overlay, [[[50, 150, 50], [10, 20, 30]]])
    np.testing.assert_array_equal(rgb, before_rgb)
    np.testing.assert_array_equal(mask, before_mask)
    assert not np.shares_memory(overlay, rgb)


@pytest.mark.parametrize(
    ("mask", "kwargs"),
    [
        (np.array([[1]], dtype=np.uint8), {}),
        (np.array([[255]], dtype=np.float32), {}),
        (np.array([[255]], dtype=np.uint8), {"opacity": 1.5}),
        (np.array([[255]], dtype=np.uint8), {"color": (0, 300, 0)}),
    ],
)
def test_overlay_rejects_invalid_mask_or_style(mask, kwargs) -> None:
    with pytest.raises(ValidationError):
        compose_segmentation_overlay(
            np.zeros((1, 1, 3), dtype=np.uint8), mask, **kwargs
        )


def test_region_and_confusion_compositions_preserve_inputs() -> None:
    rgb = np.zeros((4, 4, 3), np.uint8)
    mask = np.zeros((4, 4), np.uint8); mask[1:3, 1:3] = 255
    analysis = analyze_components(mask, AnalysisSettings(True))
    assert np.any(compose_region_annotations(rgb, analysis)) and not np.any(rgb)
    truth = mask.copy(); prediction = mask.copy()
    prediction[1, 1] = 0; prediction[0, 0] = 255
    confusion = compose_confusion_overlay(rgb, prediction, truth)
    assert tuple(confusion[1, 2]) == (40, 190, 80)
    assert tuple(confusion[0, 0]) == (230, 70, 70)
    assert tuple(confusion[1, 1]) == (60, 120, 240)


def test_watershed_overlay_marks_regions_and_boundaries_without_mutation() -> None:
    rgb, mask = touching_disks()
    before_rgb, before_mask = rgb.copy(), mask.copy()
    result = separate_watershed(
        rgb, mask, WatershedSettings(True, seed_fraction=0.7)
    )

    overlay = compose_watershed_overlay(rgb, result)

    assert result.status == "applied"
    assert np.any(overlay != rgb)
    assert np.all(overlay[result.boundaries == 255] == (255, 32, 32))
    np.testing.assert_array_equal(rgb, before_rgb)
    np.testing.assert_array_equal(mask, before_mask)

