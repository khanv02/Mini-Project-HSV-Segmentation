"""Shared deterministic fixtures for segmentation feature tests."""

from pathlib import Path

import numpy as np
import pytest

from hsv_segmentation.models import InputMedia


def _media(tmp_path: Path, rgb: np.ndarray, *, frame_index=None) -> InputMedia:
    is_video = frame_index is not None
    return InputMedia(
        source_path=(tmp_path / ("gray.avi" if is_video else "gray.png")).resolve(),
        source_sha256="1" * 64,
        source_format="AVI" if is_video else "PNG",
        rgb=rgb,
        media_kind="video" if is_video else "image",
        frame_index=frame_index,
        backend="test" if is_video else None,
    )


@pytest.fixture
def exact_gray_rgb() -> np.ndarray:
    values = np.array([[0, 64, 128], [129, 200, 255]], dtype=np.uint8)
    return np.repeat(values[..., None], 3, axis=2)


@pytest.fixture
def exact_gray_media(tmp_path, exact_gray_rgb) -> InputMedia:
    return _media(tmp_path, exact_gray_rgb)


@pytest.fixture
def nearly_gray_rgb(exact_gray_rgb) -> np.ndarray:
    rgb = exact_gray_rgb.copy()
    rgb[0, 0, 2] = 1
    return rgb


@pytest.fixture
def two_level_gray_rgb() -> np.ndarray:
    values = np.array([[20, 20, 20, 20], [220, 220, 220, 220]], dtype=np.uint8)
    return np.repeat(values[..., None], 3, axis=2)


@pytest.fixture
def constant_gray_rgb() -> np.ndarray:
    return np.full((4, 5, 3), 77, dtype=np.uint8)


@pytest.fixture
def full_hd_gray_rgb() -> np.ndarray:
    row = np.linspace(0, 255, 1920, dtype=np.uint8)
    values = np.broadcast_to(row, (1080, 1920))
    return np.repeat(values[..., None], 3, axis=2)
