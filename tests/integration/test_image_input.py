"""Image decoding and candidate-session integration tests."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from hsv_segmentation.application.session import ImageSession
from hsv_segmentation.errors import DecodeError, InputError
from hsv_segmentation.io.images import load_image
from hsv_segmentation.models import HSVThresholdSet, MAX_IMAGE_PIXELS


def _save(path: Path, array: np.ndarray, mode: str, **options) -> None:
    Image.fromarray(array, mode=mode).save(path, **options)


@pytest.mark.parametrize(("suffix", "format_name"), [(".png", "PNG"), (".bmp", "BMP")])
def test_lossless_rgb_inputs_decode_exactly(tmp_path, suffix, format_name) -> None:
    rgb = np.array([[[255, 0, 0], [1, 2, 3]], [[0, 255, 0], [0, 0, 255]]], dtype=np.uint8)
    path = (tmp_path / f"sample{suffix}").resolve()
    _save(path, rgb, "RGB")

    media = load_image(path)

    assert media.source_path == path
    assert media.source_format == format_name
    assert media.media_kind == "image"
    assert len(media.source_sha256) == 64
    np.testing.assert_array_equal(media.rgb, rgb)


def test_jpeg_decodes_to_rgb_contract(tmp_path) -> None:
    rgb = np.full((8, 8, 3), [200, 100, 50], dtype=np.uint8)
    path = (tmp_path / "sample.jpg").resolve()
    _save(path, rgb, "RGB", quality=100, subsampling=0)

    media = load_image(path)

    assert media.source_format == "JPEG"
    assert media.rgb.dtype == np.uint8
    assert media.rgb.shape == rgb.shape
    np.testing.assert_allclose(media.rgb, rgb, atol=2, rtol=0)


def test_grayscale_replicates_channels(tmp_path) -> None:
    gray = np.array([[0, 127], [200, 255]], dtype=np.uint8)
    path = (tmp_path / "gray.png").resolve()
    _save(path, gray, "L")

    media = load_image(path)

    np.testing.assert_array_equal(media.rgb, np.repeat(gray[..., None], 3, axis=2))


def test_transparent_input_ignores_alpha_without_compositing(tmp_path) -> None:
    rgba = np.array([[[12, 34, 56, 0], [200, 150, 100, 128]]], dtype=np.uint8)
    path = (tmp_path / "alpha.png").resolve()
    _save(path, rgba, "RGBA")

    media = load_image(path)

    np.testing.assert_array_equal(media.rgb, rgba[..., :3])


def test_palette_input_is_normalized_to_stored_rgb(tmp_path) -> None:
    palette = Image.new("P", (2, 1))
    palette.putpalette([255, 0, 0, 0, 255, 0] + [0, 0, 0] * 254)
    palette.putdata([0, 1])
    path = (tmp_path / "palette.png").resolve()
    palette.save(path)

    media = load_image(path)

    np.testing.assert_array_equal(media.rgb, [[[255, 0, 0], [0, 255, 0]]])


@pytest.mark.parametrize("name", ["missing.png", "unsupported.gif"])
def test_missing_or_unsupported_input_reports_actionable_error(tmp_path, name) -> None:
    path = (tmp_path / name).resolve()
    if path.suffix == ".gif":
        Image.new("RGB", (1, 1), "red").save(path)
    with pytest.raises(InputError, match="PNG, JPEG, or BMP"):
        load_image(path)


def test_corrupt_supported_file_reports_decode_error(tmp_path) -> None:
    path = (tmp_path / "broken.png").resolve()
    path.write_bytes(b"not an image")
    with pytest.raises(DecodeError, match="decode"):
        load_image(path)


def test_high_bit_depth_input_is_rejected_instead_of_rescaled(tmp_path) -> None:
    path = (tmp_path / "high-depth.png").resolve()
    Image.fromarray(np.array([[1000]], dtype=np.uint16)).save(path)
    with pytest.raises(InputError, match="8-bit"):
        load_image(path)


def test_dimension_limit_is_checked_before_pixel_conversion(tmp_path, monkeypatch) -> None:
    path = (tmp_path / "small.png").resolve()
    Image.new("RGB", (1, 1)).save(path)

    class OversizedHeader:
        format = "PNG"
        mode = "RGB"
        size = (MAX_IMAGE_PIXELS + 1, 1)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def load(self):
            raise AssertionError("pixel decoding must not start")

    monkeypatch.setattr("hsv_segmentation.io.images.Image.open", lambda _path: OversizedHeader())
    with pytest.raises(InputError, match="pixel limit"):
        load_image(path)


def test_cancelled_or_failed_open_preserves_previous_session(tmp_path) -> None:
    valid = (tmp_path / "valid.png").resolve()
    _save(valid, np.array([[[255, 0, 0]]], dtype=np.uint8), "RGB")
    session = ImageSession()
    first = session.open_image(valid)
    prior_source = session.source
    prior_result = session.result

    assert session.open_image(None) is prior_result
    assert session.source is prior_source
    with pytest.raises(InputError):
        session.open_image((tmp_path / "missing.png").resolve())
    assert session.source is prior_source
    assert session.result is prior_result
    assert first is prior_result


def test_subsequent_open_retains_valid_thresholds(tmp_path) -> None:
    first_path = (tmp_path / "first.png").resolve()
    second_path = (tmp_path / "second.bmp").resolve()
    _save(first_path, np.array([[[255, 0, 0]]], dtype=np.uint8), "RGB")
    _save(second_path, np.array([[[0, 255, 0]]], dtype=np.uint8), "RGB")
    session = ImageSession()
    session.open_image(first_path)
    thresholds = HSVThresholdSet(lower_h_deg=350, upper_h_deg=10, parameter_revision=1)
    session.set_thresholds(thresholds)

    result = session.open_image(second_path)

    assert result.thresholds is thresholds
    assert session.thresholds is thresholds
