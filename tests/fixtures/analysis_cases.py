"""Deterministic masks with hand-derived object/evaluation outcomes."""

import numpy as np


def rectangles_with_noise() -> np.ndarray:
    mask = np.zeros((10, 12), dtype=np.uint8)
    mask[1:3, 1:3] = 255       # area 4, centroid (1.5, 1.5)
    mask[5:8, 7:10] = 255      # area 9, centroid (8, 6)
    mask[0, 11] = 255          # area 1
    return mask


def diagonal_pixels() -> np.ndarray:
    mask = np.zeros((3, 3), dtype=np.uint8)
    mask[0, 0] = mask[1, 1] = 255
    return mask


def touching_disks(size: int = 96) -> tuple[np.ndarray, np.ndarray]:
    """Return RGB source and overlapping-disk foreground with two thick lobes."""
    y, x = np.ogrid[:size, :size]
    left = (x - 30) ** 2 + (y - 48) ** 2 <= 23 ** 2
    right = (x - 66) ** 2 + (y - 48) ** 2 <= 23 ** 2
    mask = np.where(left | right, 255, 0).astype(np.uint8)
    rgb = np.zeros((size, size, 3), dtype=np.uint8)
    rgb[mask == 255] = (220, 70, 40)
    return rgb, mask


def partial_overlap_masks() -> tuple[np.ndarray, np.ndarray]:
    prediction = np.array([[255, 255], [255, 0]], dtype=np.uint8)
    truth = np.array([[255, 255], [0, 255]], dtype=np.uint8)
    return prediction, truth
