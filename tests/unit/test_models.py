"""Verify shared data contracts before any GUI or algorithm is implemented."""

from dataclasses import FrozenInstanceError, replace
import subprocess
import sys

import numpy as np
import pytest

from hsv_segmentation.errors import ValidationError
from hsv_segmentation.models import (
    HSVThresholdSet,
    InputMedia,
    MAX_IMAGE_PIXELS,
    ProcessingRequest,
    SegmentationResult,
    validate_rgb,
)


def make_media(tmp_path, **changes):
    fields = dict(
        source_path=tmp_path / "source.png",
        source_sha256="a" * 64,
        source_format="PNG",
        rgb=np.array([[[255, 0, 0], [0, 255, 0]]], dtype=np.uint8),
    )
    fields.update(changes)
    return InputMedia(**fields)


def test_default_and_wrapped_thresholds_are_preserved():
    default = HSVThresholdSet()
    assert default.as_dict() == dict(
        lower_h_deg=0, upper_h_deg=360, lower_s_pct=0,
        upper_s_pct=100, lower_v_pct=0, upper_v_pct=100,
    )
    assert replace(default, lower_h_deg=350, upper_h_deg=10).wraps_hue
    assert not replace(default, lower_h_deg=0, upper_h_deg=0).wraps_hue
    assert replace(default, lower_s_pct=100).lower_s_pct == 100
    assert default.parameter_revision == 0


@pytest.mark.parametrize("field,value", [
    ("lower_h_deg", -1), ("lower_h_deg", 360), ("upper_h_deg", 361),
    ("upper_h_deg", -1), ("lower_s_pct", -1), ("upper_s_pct", 101),
    ("lower_v_pct", -1), ("upper_v_pct", 101), ("lower_h_deg", True),
    ("upper_h_deg", np.bool_(True)), ("lower_s_pct", 0.0),
    ("upper_v_pct", float("inf")), ("lower_v_pct", float("nan")),
    ("lower_h_deg", "10"), ("upper_h_deg", None),
    ("parameter_revision", -1), ("parameter_revision", True),
])
def test_invalid_threshold_values_identify_the_field(field, value):
    with pytest.raises(ValidationError) as error:
        replace(HSVThresholdSet(), **{field: value})
    assert error.value.field == field


@pytest.mark.parametrize("lower,upper", [
    ("lower_s_pct", "upper_s_pct"), ("lower_v_pct", "upper_v_pct"),
])
def test_saturation_and_value_intervals_must_be_ordered(lower, upper):
    with pytest.raises(ValidationError) as error:
        replace(HSVThresholdSet(), **{lower: 80, upper: 20})
    assert error.value.field == lower


def test_threshold_snapshots_are_immutable_and_serializable():
    thresholds = HSVThresholdSet(lower_h_deg=np.int64(20), parameter_revision=3)
    assert type(thresholds.lower_h_deg) is int
    with pytest.raises(FrozenInstanceError):
        thresholds.upper_h_deg = 10
    external = thresholds.as_dict()
    external["upper_h_deg"] = 1
    assert thresholds.upper_h_deg == 360
    assert "parameter_revision" not in external


def test_media_has_derived_dimensions_and_owned_readonly_pixels(tmp_path):
    rgb = np.array([[[255, 0, 0], [0, 255, 0]]], dtype=np.uint8)
    media = make_media(tmp_path, rgb=rgb)
    assert (media.width, media.height) == (2, 1)
    assert media.media_kind == "image" and media.frame_index is None
    assert media.session_id != make_media(tmp_path).session_id
    rgb.fill(0)
    assert media.rgb[0, 0, 0] == 255
    with pytest.raises(ValueError):
        media.rgb[0, 0, 0] = 0
    with pytest.raises(ValueError):
        media.rgb.setflags(write=True)


@pytest.mark.parametrize("rgb", [
    [], np.empty((0, 2, 3), dtype=np.uint8), np.zeros((2, 2), dtype=np.uint8),
    np.zeros((2, 2, 4), dtype=np.uint8), np.zeros((2, 2, 3), dtype=np.float64),
    np.broadcast_to(np.uint8(0), (3000, 4001, 3)),
])
def test_invalid_rgb_is_rejected_without_normalization(rgb):
    with pytest.raises(ValidationError, match="rgb"):
        validate_rgb(rgb)


def test_rgb_pixel_limit_is_inclusive_without_allocating_large_image():
    rgb = np.broadcast_to(np.uint8(0), (3000, 4000, 3))
    assert rgb.shape[0] * rgb.shape[1] == MAX_IMAGE_PIXELS
    assert validate_rgb(rgb) == (3000, 4000)


@pytest.mark.parametrize("changes,field", [
    ({"source_path": "relative.png"}, "source_path"),
    ({"source_sha256": "not-a-hash"}, "source_sha256"),
    ({"source_sha256": "A" * 64}, "source_sha256"),
    ({"session_id": ""}, "session_id"),
    ({"source_format": "GIF"}, "source_format"),
    ({"media_kind": "camera"}, "media_kind"),
    ({"frame_index": 0}, "frame_index"),
    ({"backend": "FFMPEG"}, "backend"),
    ({"media_kind": "video", "source_format": "MP4"}, "frame_index"),
    ({"media_kind": "video", "source_format": "MP4", "frame_index": -1}, "frame_index"),
    ({"media_kind": "video", "source_format": "MP4", "frame_index": 0}, "backend"),
])
def test_media_identity_constraints(tmp_path, changes, field):
    with pytest.raises(ValidationError) as error:
        make_media(tmp_path, **changes)
    assert error.value.field == field


def test_request_and_result_share_the_exact_source_and_parameter_identity(tmp_path):
    media = make_media(
        tmp_path, media_kind="video", source_format="AVI", frame_index=7, backend="test"
    )
    thresholds = HSVThresholdSet(parameter_revision=2)
    request = ProcessingRequest(media, thresholds, request_revision=4)
    mask = np.array([[255, 0]], dtype=np.uint8)
    segmented = np.array([[[255, 0, 0], [0, 0, 0]]], dtype=np.uint8)
    result = SegmentationResult(media, thresholds, mask, segmented, request_revision=4)
    for snapshot in (request, result):
        assert snapshot.session_id == media.session_id
        assert snapshot.frame_index == 7
        assert snapshot.parameter_revision == 2
        assert snapshot.request_revision == 4
    assert result.original_rgb is media.rgb
    assert (result.height, result.width) == (1, 2)
    mask.fill(0)
    segmented.fill(0)
    assert result.mask[0, 0] == 255
    assert result.segmented_rgb[0, 0, 0] == 255
    for array in (result.mask, result.segmented_rgb):
        with pytest.raises(ValueError):
            array.setflags(write=True)


@pytest.mark.parametrize("mask,segmented", [
    (np.array([[1, 0]], dtype=np.uint8), [[[255, 0, 0], [0, 0, 0]]]),
    (np.array([[255]], dtype=np.uint8), [[[255, 0, 0], [0, 0, 0]]]),
    (np.array([[255, 0]], dtype=np.float64), [[[255, 0, 0], [0, 0, 0]]]),
    (np.array([[255, 0]], dtype=np.uint8), [[[254, 0, 0], [0, 0, 0]]]),
    (np.array([[255, 0]], dtype=np.uint8), [[[255, 0, 0], [1, 0, 0]]]),
])
def test_result_rejects_inconsistent_mask_or_extracted_pixels(tmp_path, mask, segmented):
    with pytest.raises(ValidationError):
        SegmentationResult(
            make_media(tmp_path), HSVThresholdSet(), mask, np.array(segmented, dtype=np.uint8)
        )


@pytest.mark.parametrize("revision", [-1, True, 1.5])
def test_request_revision_cannot_be_invalid(tmp_path, revision):
    with pytest.raises(ValidationError, match="request_revision"):
        ProcessingRequest(make_media(tmp_path), HSVThresholdSet(), revision)


def test_shared_models_import_without_loading_gui_or_file_adapters():
    code = (
        "import sys; import hsv_segmentation.models, hsv_segmentation.errors; "
        "assert not any(n in sys.modules for n in "
        "['tkinter','PIL','cv2','hsv_segmentation.gui','hsv_segmentation.io'])"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
