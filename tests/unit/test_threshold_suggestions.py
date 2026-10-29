"""Color sampling and suggested-threshold tests independent of the GUI."""

import numpy as np
import pytest

from hsv_segmentation.errors import ValidationError
from hsv_segmentation.processing.threshold_suggestions import (
    ColorSample,
    HSV_PRESETS,
    sample_color,
    sample_color_region,
    sample_colors,
    suggest_thresholds,
)


def test_sample_color_reports_source_coordinates_rgb_and_hsv() -> None:
    rgb = np.array([[[0, 0, 0], [255, 0, 0]], [[0, 255, 0], [0, 0, 255]]], dtype=np.uint8)

    sample = sample_color(rgb, 0, 1)

    assert sample.x == 0 and sample.y == 1
    assert sample.rgb == (0, 255, 0)
    assert sample.hue_deg == pytest.approx(120.0)
    assert sample.saturation_pct == pytest.approx(100.0)
    assert sample.value_pct == pytest.approx(100.0)


@pytest.mark.parametrize(("x", "y"), [(-1, 0), (2, 0), (0, -1), (0, 2), (0.5, 0)])
def test_sample_color_rejects_invalid_coordinates(x, y) -> None:
    with pytest.raises(ValidationError):
        sample_color(np.zeros((2, 2, 3), dtype=np.uint8), x, y)


def test_suggestion_clamps_sv_and_wraps_hue_around_red() -> None:
    sample = ColorSample(3, 4, (255, 0, 0), 2.0, 96.0, 94.0)

    thresholds = suggest_thresholds(sample)

    assert thresholds.lower_h_deg == 347
    assert thresholds.upper_h_deg == 17
    assert thresholds.wraps_hue
    assert thresholds.lower_s_pct == 81
    assert thresholds.upper_s_pct == 100
    assert thresholds.lower_v_pct == 79
    assert thresholds.upper_v_pct == 100


def test_achromatic_sample_suggests_full_hue_range() -> None:
    sample = ColorSample(0, 0, (128, 128, 128), 0.0, 0.0, 50.2)

    thresholds = suggest_thresholds(sample)

    assert (thresholds.lower_h_deg, thresholds.upper_h_deg) == (0, 360)
    assert (thresholds.lower_s_pct, thresholds.upper_s_pct) == (0, 15)
    assert (thresholds.lower_v_pct, thresholds.upper_v_pct) == (35, 66)


def test_basic_presets_are_valid_and_include_reset_range() -> None:
    assert tuple(HSV_PRESETS) == ("All colors", "Red", "Yellow", "Green", "Blue")
    assert HSV_PRESETS["All colors"].as_dict() == {
        "lower_h_deg": 0,
        "upper_h_deg": 360,
        "lower_s_pct": 0,
        "upper_s_pct": 100,
        "lower_v_pct": 0,
        "upper_v_pct": 100,
    }
    assert HSV_PRESETS["Red"].wraps_hue


def test_region_sample_uses_short_circular_hue_arc_and_roi_spread() -> None:
    rgb = np.array(
        [[[255, 0, 43], [255, 0, 0], [255, 43, 0]], [[100, 0, 17], [128, 0, 0], [100, 17, 0]]],
        dtype=np.uint8,
    )

    sample = sample_color_region(rgb, 0, 0, 3, 2)

    assert sample.pixel_count == 6
    assert sample.thresholds.wraps_hue
    assert sample.thresholds.lower_h_deg >= 340
    assert sample.thresholds.upper_h_deg <= 20
    assert sample.thresholds.lower_s_pct == 95
    assert sample.thresholds.upper_s_pct == 100
    assert sample.thresholds.lower_v_pct < sample.thresholds.upper_v_pct


def test_achromatic_region_uses_full_hue_range() -> None:
    rgb = np.array([[[64, 64, 64], [192, 192, 192]]], dtype=np.uint8)

    sample = sample_color_region(rgb, 0, 0, 2, 1)

    assert (sample.thresholds.lower_h_deg, sample.thresholds.upper_h_deg) == (0, 360)
    assert sample.pixel_count == 2


def test_multi_sample_combines_sparse_pixels_and_short_hue_arc() -> None:
    rgb = np.array(
        [[[255, 0, 43], [255, 0, 0], [255, 43, 0], [128, 0, 0]]],
        dtype=np.uint8,
    )

    sample = sample_colors(rgb, ((0, 0), (1, 0), (2, 0), (3, 0)))

    assert sample.pixel_count == 4
    assert sample.thresholds.wraps_hue
    assert sample.thresholds.lower_h_deg >= 340
    assert sample.thresholds.upper_h_deg <= 20
    assert sample.thresholds.lower_s_pct == 95
    assert sample.thresholds.upper_s_pct == 100
    assert sample.thresholds.lower_v_pct <= 46
    assert sample.thresholds.upper_v_pct == 100


@pytest.mark.parametrize("coordinates", [(), ((0, 0),), ((0, 0),) * 5, ((0, 0, 1), (1, 0))])
def test_multi_sample_requires_two_to_four_coordinate_pairs(coordinates) -> None:
    with pytest.raises(ValidationError, match="coordinates"):
        sample_colors(np.zeros((2, 2, 3), dtype=np.uint8), coordinates)


@pytest.mark.parametrize(
    "bounds",
    [(-1, 0, 1, 1), (0, 0, 0, 1), (0, 0, 3, 1), (0, 1, 1, 1)],
)
def test_region_sample_rejects_invalid_or_empty_bounds(bounds) -> None:
    with pytest.raises(ValidationError, match="roi"):
        sample_color_region(np.zeros((2, 2, 3), dtype=np.uint8), *bounds)

