"""Lossless full-resolution PNG export contract."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from hsv_segmentation.errors import WriteError
from hsv_segmentation.io.export import save_mask_png, save_result_png


def test_mask_png_round_trip_is_source_sized_and_strictly_binary(tmp_path) -> None:
    mask = np.array([[0, 255, 0], [255, 255, 0]], dtype=np.uint8)
    path = (tmp_path / "mask.png").resolve()

    saved = save_mask_png(mask, path)

    assert saved == path
    with Image.open(path) as image:
        assert image.mode == "L"
        assert image.size == (3, 2)
        np.testing.assert_array_equal(np.asarray(image), mask)
        assert set(np.unique(np.asarray(image))) == {0, 255}


def test_result_png_round_trip_preserves_exact_rgb_pixels(tmp_path) -> None:
    rgb = np.array(
        [
            [[255, 0, 0], [0, 0, 0], [1, 2, 3]],
            [[0, 255, 0], [0, 0, 255], [250, 251, 252]],
        ],
        dtype=np.uint8,
    )
    path = (tmp_path / "result.png").resolve()

    saved = save_result_png(rgb, path)

    assert saved == path
    with Image.open(path) as image:
        assert image.mode == "RGB"
        assert image.size == (3, 2)
        np.testing.assert_array_equal(np.asarray(image), rgb)


@pytest.mark.parametrize(
    ("writer", "array"),
    [
        (save_mask_png, np.array([[0, 1]], dtype=np.uint8)),
        (save_mask_png, np.zeros((1, 1, 1), dtype=np.uint8)),
        (save_result_png, np.zeros((1, 1), dtype=np.uint8)),
        (save_result_png, np.zeros((1, 1, 3), dtype=np.float64)),
    ],
)
def test_export_rejects_invalid_array_contract(writer, array, tmp_path) -> None:
    with pytest.raises(WriteError, match="invalid output data"):
        writer(array, (tmp_path / "invalid.png").resolve())


def test_export_refuses_unconfirmed_overwrite_without_changing_file(tmp_path) -> None:
    path = (tmp_path / "existing.png").resolve()
    path.write_bytes(b"original bytes")

    with pytest.raises(WriteError, match="already exists"):
        save_mask_png(np.array([[255]], dtype=np.uint8), path)

    assert path.read_bytes() == b"original bytes"


def test_export_replaces_existing_file_only_when_overwrite_is_explicit(tmp_path) -> None:
    path = (tmp_path / "existing.png").resolve()
    path.write_bytes(b"old bytes")
    mask = np.array([[0, 255]], dtype=np.uint8)

    save_mask_png(mask, path, overwrite=True)

    np.testing.assert_array_equal(np.asarray(Image.open(path)), mask)


def test_export_wraps_destination_failure_and_preserves_existing_file(
    tmp_path, monkeypatch
) -> None:
    path = (tmp_path / "existing.png").resolve()
    path.write_bytes(b"original bytes")

    def fail_replace(source, destination):
        raise PermissionError("simulated denied write")

    monkeypatch.setattr("hsv_segmentation.io.export.os.replace", fail_replace)
    with pytest.raises(WriteError) as caught:
        save_result_png(
            np.array([[[4, 5, 6]]], dtype=np.uint8), path, overwrite=True
        )

    assert caught.value.path == path
    assert caught.value.operation == "save result PNG"
    assert "simulated denied write" in str(caught.value)
    assert path.read_bytes() == b"original bytes"


def test_export_requires_png_destination(tmp_path) -> None:
    with pytest.raises(WriteError, match=r"\.png"):
        save_mask_png(
            np.array([[0]], dtype=np.uint8), (tmp_path / "mask.jpg").resolve()
        )
