from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from hsv_segmentation.errors import DecodeError, InputError, ValidationError
from hsv_segmentation.io.ground_truth import load_ground_truth
from hsv_segmentation.models import InputMedia


def source(tmp_path: Path) -> InputMedia:
    return InputMedia(tmp_path.resolve() / "source.png", "a" * 64, "PNG", np.zeros((2, 3, 3), np.uint8))


def test_loads_lossless_grayscale_with_strict_threshold(tmp_path) -> None:
    path = tmp_path / "truth.png"
    Image.fromarray(np.array([[0, 1, 2], [255, 1, 0]], np.uint8)).save(path)
    truth = load_ground_truth(path, source(tmp_path), threshold=1, truth_revision=3)
    np.testing.assert_array_equal(truth.mask, [[0, 0, 255], [255, 0, 0]])
    assert truth.truth_revision == 3 and len(truth.pixel_sha256) == 64


def test_accepts_equal_rgb_and_ignores_alpha(tmp_path) -> None:
    path = tmp_path / "truth.png"
    rgba = np.zeros((2, 3, 4), np.uint8); rgba[..., :3] = 255
    Image.fromarray(rgba, "RGBA").save(path)
    truth = load_ground_truth(path, source(tmp_path))
    assert truth.alpha_ignored and np.all(truth.mask == 255)


def test_rejects_colored_mismatch_and_jpeg(tmp_path) -> None:
    colored = tmp_path / "colored.png"
    rgb = np.zeros((2, 3, 3), np.uint8); rgb[0, 0] = (255, 0, 0)
    Image.fromarray(rgb).save(colored)
    with pytest.raises(InputError, match="channels"):
        load_ground_truth(colored, source(tmp_path))
    wrong = tmp_path / "wrong.png"; Image.fromarray(np.zeros((3, 3), np.uint8)).save(wrong)
    with pytest.raises(ValidationError, match="dimensions"):
        load_ground_truth(wrong, source(tmp_path))
    jpeg = tmp_path / "truth.jpg"; Image.fromarray(np.zeros((2, 3), np.uint8)).save(jpeg)
    with pytest.raises(InputError, match="PNG or BMP"):
        load_ground_truth(jpeg, source(tmp_path))


def test_palette_and_binary_masks_normalize_without_resizing(tmp_path) -> None:
    palette_path = tmp_path / "palette.png"
    palette = Image.fromarray(np.array([[0, 1, 0], [1, 0, 1]], np.uint8), "P")
    grayscale_palette = []
    for value in range(256):
        grayscale_palette.extend((value, value, value))
    palette.putpalette(grayscale_palette)
    palette.save(palette_path)
    truth = load_ground_truth(palette_path, source(tmp_path), threshold=0)
    np.testing.assert_array_equal(truth.mask, [[0, 255, 0], [255, 0, 255]])

    binary_path = tmp_path / "binary.bmp"
    Image.fromarray(np.array([[0, 255, 0], [255, 255, 0]], np.uint8)).convert("1").save(binary_path)
    np.testing.assert_array_equal(
        load_ground_truth(binary_path, source(tmp_path)).mask,
        [[0, 255, 0], [255, 255, 0]],
    )


def test_corrupt_truth_reports_decode_error(tmp_path) -> None:
    corrupt = tmp_path / "truth.png"
    corrupt.write_bytes(b"not a png")
    with pytest.raises(DecodeError, match="could not be decoded"):
        load_ground_truth(corrupt, source(tmp_path))
