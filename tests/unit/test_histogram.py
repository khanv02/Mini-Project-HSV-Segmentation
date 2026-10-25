"""Analytical contracts for pure HSV histogram counting."""

import numpy as np
import pytest

from hsv_segmentation.errors import ValidationError
from hsv_segmentation.models import HSVHistogram
from hsv_segmentation.processing.histogram import compute_hsv_histogram


def test_histogram_uses_exact_bins_and_hue_cutoff_without_mutation() -> None:
    hsv = np.array(
        [[
            [0.0, 0.0, 0.0],
            [10.9, 4.999, 100.0],
            [359.9, 5.0, 99.9],
            [120.0, 5.9, 50.2],
            [240.0, 100.0, 100.0],
        ]],
        dtype=np.float64,
    )
    original = hsv.copy()

    histogram = compute_hsv_histogram(hsv)

    assert histogram.excluded_hue_count == 2
    assert histogram.hue_counts[359] == 1
    assert histogram.hue_counts[120] == 1
    assert histogram.hue_counts[240] == 1
    assert histogram.hue_counts.sum() == 3
    assert histogram.saturation_counts[0] == 1
    assert histogram.saturation_counts[4] == 1
    assert histogram.saturation_counts[5] == 2
    assert histogram.saturation_counts[100] == 1
    assert histogram.value_counts[0] == 1
    assert histogram.value_counts[50] == 1
    assert histogram.value_counts[99] == 1
    assert histogram.value_counts[100] == 2
    assert histogram.pixel_count == 5
    np.testing.assert_array_equal(hsv, original)


def test_neutral_image_reports_empty_hue_and_all_sv_pixels() -> None:
    hsv = np.array([[[0.0, 0.0, 10.0], [0.0, 0.0, 90.0]]], dtype=np.float64)

    histogram = compute_hsv_histogram(hsv)

    assert histogram.hue_counts.sum() == 0
    assert histogram.excluded_hue_count == 2
    assert histogram.saturation_counts[0] == 2
    assert histogram.value_counts.sum() == 2


def test_histogram_result_owns_immutable_counts() -> None:
    source = np.ones(360, dtype=np.int64)
    with pytest.raises(ValidationError):
        HSVHistogram(
            hue_counts=source,
            saturation_counts=np.array([1] + [0] * 100, dtype=np.int64),
            value_counts=np.array([1] + [0] * 100, dtype=np.int64),
            excluded_hue_count=-359,
        )


@pytest.mark.parametrize(
    "hsv",
    [
        np.zeros((1, 1, 3), dtype=np.float32),
        np.zeros((1, 3), dtype=np.float64),
        np.array([[[360.0, 10.0, 10.0]]], dtype=np.float64),
        np.array([[[0.0, -0.1, 10.0]]], dtype=np.float64),
        np.array([[[0.0, 10.0, np.nan]]], dtype=np.float64),
    ],
)
def test_histogram_rejects_invalid_hsv(hsv: np.ndarray) -> None:
    with pytest.raises(ValidationError):
        compute_hsv_histogram(hsv)


def test_histogram_counts_are_read_only_and_detached() -> None:
    hsv = np.array([[[30.0, 50.0, 75.0]]], dtype=np.float64)
    histogram = compute_hsv_histogram(hsv)

    with pytest.raises(ValueError):
        histogram.hue_counts[30] = 9
    with pytest.raises(ValueError):
        histogram.hue_counts.setflags(write=True)
