"""Mode-aware processing integration tests."""

from dataclasses import replace

import numpy as np
import pytest

from hsv_segmentation.application.session import process_source
from hsv_segmentation.errors import ValidationError
from hsv_segmentation.models import (
    AnalysisSettings, GrayscaleSettings, HSVThresholdSet, MorphologySettings,
    SegmentationMode,
)


def test_manual_grayscale_flows_through_shared_pipeline(exact_gray_media):
    settings = GrayscaleSettings(manual_threshold=128, polarity="bright", settings_revision=2)
    result = process_source(
        exact_gray_media, HSVThresholdSet(), 4,
        segmentation_mode=SegmentationMode.GRAYSCALE,
        grayscale_settings=settings,
        analysis_settings=AnalysisSettings(enabled=True),
        settings_revision=2,
    )
    expected = np.where(exact_gray_media.rgb[..., 0] > 128, 255, 0).astype(np.uint8)
    assert np.array_equal(result.original_mask, expected)
    assert result.segmentation_mode == "grayscale"
    assert result.grayscale_eligibility.eligible
    assert result.analysis is not None


def test_otsu_grayscale_records_resolved_outcome(tmp_path, two_level_gray_rgb):
    from hsv_segmentation.models import InputMedia
    source = InputMedia(
        (tmp_path / "two.png").resolve(), "b" * 64, "PNG", two_level_gray_rgb
    )
    result = process_source(
        source, HSVThresholdSet(), 1,
        segmentation_mode="grayscale",
        grayscale_settings=GrayscaleSettings(threshold_source="otsu"),
    )
    assert result.otsu_outcome.status == "applied"
    assert result.otsu_outcome.threshold == 20


def test_constant_otsu_and_color_grayscale_are_rejected(
    tmp_path, constant_gray_rgb, nearly_gray_rgb
):
    from hsv_segmentation.models import InputMedia
    constant = InputMedia((tmp_path / "c.png").resolve(), "c" * 64, "PNG", constant_gray_rgb)
    color = InputMedia((tmp_path / "n.png").resolve(), "d" * 64, "PNG", nearly_gray_rgb)
    with pytest.raises(ValidationError, match="meaningful split"):
        process_source(
            constant, HSVThresholdSet(), 1, segmentation_mode="grayscale",
            grayscale_settings=GrayscaleSettings(threshold_source="otsu"),
        )
    with pytest.raises(ValidationError, match="equal"):
        process_source(color, HSVThresholdSet(), 1, segmentation_mode="grayscale")


def test_default_hsv_result_is_backward_compatible(exact_gray_media):
    result = process_source(exact_gray_media, HSVThresholdSet(), 1)
    assert result.segmentation_mode == "hsv"
    assert result.otsu_outcome.status == "not_requested"
    assert np.all(result.mask == 255)
