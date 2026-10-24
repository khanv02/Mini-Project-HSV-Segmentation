"""Exact threshold, mask, extraction, and composition tests."""

from dataclasses import replace

import numpy as np
import pytest

from hsv_segmentation.errors import ValidationError
from hsv_segmentation.models import HSVThresholdSet, MAX_IMAGE_PIXELS
from hsv_segmentation.processing.segmentation import apply_mask, generate_mask, segment
from hsv_segmentation.processing.thresholds import validate_thresholds
from tests.fixtures.color_cases import (
    analytical_colors,
    red_extraction_reference,
    threshold_cases,
)


@pytest.mark.parametrize("case", threshold_cases(), ids=lambda case: case.name)
def test_threshold_membership_is_exact_and_inclusive(case) -> None:
    mask = generate_mask(case.hsv, case.bounds)
    np.testing.assert_array_equal(mask, case.expected_mask)
    assert mask.dtype == np.uint8
    assert set(np.unique(mask)).issubset({0, 255})


def test_mapping_and_model_validation_return_immutable_model() -> None:
    mapping = dict(
        lower_h_deg=350, upper_h_deg=10, lower_s_pct=20,
        upper_s_pct=80, lower_v_pct=30, upper_v_pct=90,
    )
    from_mapping = validate_thresholds(mapping)
    from_model = validate_thresholds(HSVThresholdSet(**mapping, parameter_revision=7))

    assert isinstance(from_mapping, HSVThresholdSet)
    assert from_mapping.as_dict() == mapping
    assert from_model.parameter_revision == 7


@pytest.mark.parametrize(
    "change",
    [
        {"lower_h_deg": True}, {"upper_h_deg": False},
        {"lower_s_pct": 1.5}, {"upper_s_pct": float("inf")},
        {"lower_v_pct": float("nan")}, {"upper_v_pct": "100"},
        {"lower_h_deg": -1}, {"lower_h_deg": 360},
        {"upper_h_deg": -1}, {"upper_h_deg": 361},
        {"lower_s_pct": -1}, {"upper_s_pct": 101},
        {"lower_v_pct": 70, "upper_v_pct": 60},
        {"lower_s_pct": 80, "upper_s_pct": 70},
    ],
)
def test_invalid_threshold_values_are_rejected(change) -> None:
    values = HSVThresholdSet().as_dict()
    values.update(change)
    with pytest.raises(ValidationError):
        validate_thresholds(values)


@pytest.mark.parametrize(
    "mapping",
    [
        {},
        {"lower_h_deg": 0},
        {**HSVThresholdSet().as_dict(), "unexpected": 1},
    ],
)
def test_missing_or_extra_threshold_fields_are_rejected(mapping) -> None:
    with pytest.raises(ValidationError, match="thresholds"):
        validate_thresholds(mapping)


@pytest.mark.parametrize(
    "hsv",
    [
        [[[0.0, 0.0, 0.0]]],
        np.zeros((1, 1, 3), dtype=np.float32),
        np.zeros((1, 1), dtype=np.float64),
        np.zeros((1, 1, 4), dtype=np.float64),
        np.zeros((0, 1, 3), dtype=np.float64),
        np.array([[[np.nan, 0.0, 0.0]]], dtype=np.float64),
        np.array([[[360.0, 0.0, 0.0]]], dtype=np.float64),
        np.array([[[-0.1, 0.0, 0.0]]], dtype=np.float64),
        np.array([[[0.0, 100.1, 0.0]]], dtype=np.float64),
        np.array([[[0.0, 0.0, -0.1]]], dtype=np.float64),
    ],
)
def test_invalid_hsv_arrays_are_rejected(hsv) -> None:
    with pytest.raises(ValidationError, match="hsv"):
        generate_mask(hsv, HSVThresholdSet())


def test_hsv_pixel_limit_is_enforced_without_large_allocation() -> None:
    oversized = np.broadcast_to(
        np.zeros((1, 1, 3), dtype=np.float64), (1, MAX_IMAGE_PIXELS + 1, 3)
    )
    with pytest.raises(ValidationError, match="pixel limit"):
        generate_mask(oversized, HSVThresholdSet())


def test_apply_mask_retains_selected_rgb_and_blacks_excluded_pixels() -> None:
    rgb, mask, expected = red_extraction_reference()
    before_rgb = rgb.copy()
    before_mask = mask.copy()
    actual = apply_mask(rgb, mask)

    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(rgb, before_rgb)
    np.testing.assert_array_equal(mask, before_mask)
    assert not np.shares_memory(actual, rgb)


@pytest.mark.parametrize(
    ("rgb", "mask"),
    [
        (np.zeros((1, 1, 3), dtype=np.float32), np.zeros((1, 1), dtype=np.uint8)),
        (np.zeros((1, 1, 3), dtype=np.uint8), np.zeros((1, 1), dtype=np.float32)),
        (np.zeros((1, 1, 3), dtype=np.uint8), np.zeros((2, 1), dtype=np.uint8)),
        (np.zeros((1, 1, 3), dtype=np.uint8), np.array([[1]], dtype=np.uint8)),
    ],
)
def test_apply_mask_rejects_type_shape_and_nonbinary_values(rgb, mask) -> None:
    with pytest.raises(ValidationError):
        apply_mask(rgb, mask)


def test_segment_composes_conversion_mask_and_extraction_without_mutation() -> None:
    rgb, expected_mask, expected_rgb = red_extraction_reference()
    thresholds = HSVThresholdSet(
        lower_h_deg=350, upper_h_deg=10, lower_s_pct=50,
        upper_s_pct=100, lower_v_pct=0, upper_v_pct=100,
    )
    before = rgb.copy()
    mask, extracted = segment(rgb, thresholds)

    np.testing.assert_array_equal(mask, expected_mask)
    np.testing.assert_array_equal(extracted, expected_rgb)
    np.testing.assert_array_equal(rgb, before)


def test_generate_mask_returns_owned_output_and_does_not_mutate_hsv() -> None:
    hsv = analytical_colors().expected_hsv.copy()
    before = hsv.copy()
    mask = generate_mask(hsv, HSVThresholdSet())
    mask[:] = 0

    np.testing.assert_array_equal(hsv, before)
    assert not np.shares_memory(mask, hsv)
