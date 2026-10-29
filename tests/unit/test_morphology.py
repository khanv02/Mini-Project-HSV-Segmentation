"""Opening, Closing, and disabled morphology behavior."""

import numpy as np
import pytest

from hsv_segmentation.errors import ValidationError
from hsv_segmentation.models import MorphologySettings
from hsv_segmentation.processing.morphology import apply_morphology


def test_opening_removes_isolated_foreground_noise() -> None:
    mask = np.zeros((7, 7), dtype=np.uint8)
    mask[2:5, 2:5] = 255
    mask[0, 0] = 255

    result = apply_morphology(
        mask, MorphologySettings(True, "opening", 3)
    )

    expected = np.zeros((7, 7), dtype=np.uint8)
    expected[2:5, 2:5] = 255
    np.testing.assert_array_equal(result, expected)


def test_closing_fills_small_background_hole() -> None:
    mask = np.zeros((7, 7), dtype=np.uint8)
    mask[1:6, 1:6] = 255
    mask[3, 3] = 0

    result = apply_morphology(
        mask, MorphologySettings(True, "closing", 3)
    )

    expected = np.zeros((7, 7), dtype=np.uint8)
    expected[1:6, 1:6] = 255
    np.testing.assert_array_equal(result, expected)


def test_closing_preserves_foreground_touching_image_border() -> None:
    mask = np.zeros((7, 7), dtype=np.uint8)
    mask[0:5, 0:5] = 255
    mask[2, 2] = 0

    result = apply_morphology(mask, MorphologySettings(True, "closing", 3))

    expected = np.zeros((7, 7), dtype=np.uint8)
    expected[0:5, 0:5] = 255
    np.testing.assert_array_equal(result, expected)


def test_opening_then_closing_matches_two_explicit_operations() -> None:
    mask = np.zeros((11, 11), dtype=np.uint8)
    mask[2:9, 2:9] = 255
    mask[5, 5] = 0
    mask[0, 0] = 255
    settings = MorphologySettings(True, "opening_closing", 3)

    combined = apply_morphology(mask, settings)
    opened = apply_morphology(mask, MorphologySettings(True, "opening", 3))
    expected = apply_morphology(
        opened, MorphologySettings(True, "closing", 3)
    )

    np.testing.assert_array_equal(combined, expected)


def test_disabled_morphology_preserves_pixels_and_returns_owned_mask() -> None:
    mask = np.array([[0, 255], [255, 0]], dtype=np.uint8)

    result = apply_morphology(mask, MorphologySettings())

    np.testing.assert_array_equal(result, mask)
    assert not np.shares_memory(result, mask)


@pytest.mark.parametrize("kernel_size", [1, 2, 4, 11, True])
def test_settings_reject_unsupported_kernel_sizes(kernel_size) -> None:
    with pytest.raises(ValidationError, match="kernel_size"):
        MorphologySettings(kernel_size=kernel_size)
