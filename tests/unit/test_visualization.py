"""Display-only segmentation overlay tests."""

import numpy as np
import pytest

from hsv_segmentation.errors import ValidationError
from hsv_segmentation.processing.visualization import compose_segmentation_overlay


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

