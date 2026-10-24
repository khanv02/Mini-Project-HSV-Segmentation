"""Unit tests for the pure RGB-to-HSV conversion contract."""

import subprocess
import sys

import numpy as np
import pytest

from hsv_segmentation.errors import ValidationError
from hsv_segmentation.models import MAX_IMAGE_PIXELS
from hsv_segmentation.processing.color import rgb_to_hsv
from tests.fixtures.color_cases import (
    ABS_HUE_TOLERANCE_DEG,
    ABS_SV_TOLERANCE_PCT,
    RELATIVE_TOLERANCE,
    analytical_colors,
    colorsys_sample,
)


def _assert_hsv_close(actual: np.ndarray, expected: np.ndarray) -> None:
    hue_error = np.abs(actual[..., 0] - expected[..., 0])
    hue_error = np.minimum(hue_error, 360.0 - hue_error)
    assert np.all(hue_error <= ABS_HUE_TOLERANCE_DEG)
    np.testing.assert_allclose(
        actual[..., 1:], expected[..., 1:], rtol=RELATIVE_TOLERANCE,
        atol=ABS_SV_TOLERANCE_PCT,
    )


def test_analytical_colors_match_hand_derived_values() -> None:
    case = analytical_colors()
    actual = rgb_to_hsv(case.rgb)

    assert actual.dtype == np.float64
    assert actual.shape == case.rgb.shape
    _assert_hsv_close(actual, case.expected_hsv)


def test_deterministic_sample_matches_independent_colorsys_oracle() -> None:
    case = colorsys_sample()
    _assert_hsv_close(rgb_to_hsv(case.rgb), case.expected_hsv)


def test_conversion_uses_rgb_channel_order() -> None:
    rgb = np.array([[[255, 0, 0], [0, 0, 255]]], dtype=np.uint8)
    actual = rgb_to_hsv(rgb)
    np.testing.assert_array_equal(actual[0, :, 0], [0.0, 240.0])


@pytest.mark.parametrize(
    "rgb",
    [
        [[0, 0, 0]],
        np.zeros((1, 1, 3), dtype=np.float32),
        np.zeros((1, 1), dtype=np.uint8),
        np.zeros((1, 1, 4), dtype=np.uint8),
        np.zeros((0, 1, 3), dtype=np.uint8),
    ],
)
def test_invalid_rgb_contract_is_rejected(rgb) -> None:
    with pytest.raises(ValidationError, match="rgb"):
        rgb_to_hsv(rgb)


def test_pixel_limit_is_checked_without_allocating_a_large_image() -> None:
    oversized = np.broadcast_to(
        np.zeros((1, 1, 3), dtype=np.uint8), (1, MAX_IMAGE_PIXELS + 1, 3)
    )
    with pytest.raises(ValidationError, match="pixel limit"):
        rgb_to_hsv(oversized)


def test_source_is_not_mutated_and_result_owns_its_data() -> None:
    rgb = analytical_colors().rgb
    before = rgb.copy()
    hsv = rgb_to_hsv(rgb)

    np.testing.assert_array_equal(rgb, before)
    assert not np.shares_memory(rgb, hsv)
    hsv[0, 0] = [1.0, 2.0, 3.0]
    np.testing.assert_array_equal(rgb, before)


def test_processing_module_does_not_import_gui_or_file_adapters() -> None:
    script = """
import sys
from hsv_segmentation.processing.color import rgb_to_hsv
for name in sys.modules:
    assert not name.startswith('hsv_segmentation.gui')
    assert not name.startswith('hsv_segmentation.io')
"""
    completed = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0, completed.stderr
