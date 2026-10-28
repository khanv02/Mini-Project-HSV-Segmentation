from pathlib import Path

import numpy as np
import pytest

from hsv_segmentation.application.session import ImageSession, process_source
from hsv_segmentation.errors import ValidationError
from hsv_segmentation.models import (
    AnalysisSettings, GroundTruth, HSVThresholdSet, InputMedia, WatershedSettings,
)


def source(tmp_path: Path) -> InputMedia:
    rgb = np.zeros((20, 20, 3), np.uint8); rgb[2:6, 2:6] = (255, 0, 0)
    return InputMedia((tmp_path / "source.png").resolve(), "a" * 64, "PNG", rgb)


def test_process_source_keeps_baseline_and_adds_optional_analysis(tmp_path) -> None:
    media = source(tmp_path)
    baseline = process_source(media, HSVThresholdSet(), 1)
    extended = process_source(
        media, HSVThresholdSet(), 2,
        analysis_settings=AnalysisSettings(True, 8, 1),
    )
    np.testing.assert_array_equal(extended.mask, baseline.mask)
    np.testing.assert_array_equal(extended.segmented_rgb, baseline.segmented_rgb)
    assert baseline.analysis is None and extended.analysis.retained_count == 1


def test_session_rejects_stale_settings_revision(tmp_path) -> None:
    media = source(tmp_path); session = ImageSession()
    candidate = process_source(media, session.thresholds, 1)
    session.commit_candidate(candidate)
    session.accept_analysis(AnalysisSettings(True))
    stale = process_source(media, session.thresholds, 2, settings_revision=0)
    assert not session.commit_result(stale)
    current = process_source(
        media, session.thresholds, 3, analysis_settings=session.analysis_settings,
        watershed_settings=session.watershed_settings,
        settings_revision=session.settings_revision,
    )
    assert session.commit_result(current)


def test_truth_binding_rejects_another_source_and_clears_on_video_advance(tmp_path) -> None:
    rgb = np.zeros((8, 8, 3), np.uint8)
    first = InputMedia(
        (tmp_path / "video.avi").resolve(), "a" * 64, "AVI", rgb,
        "video", "video-session", 0, "fixture",
    )
    session = ImageSession()
    session.commit_candidate(process_source(first, session.thresholds, 1))
    wrong = GroundTruth(
        np.zeros((8, 8), np.uint8), (tmp_path / "truth.png").resolve(),
        "b" * 64, "c" * 64, 0, False, "another-session", "a" * 64, 0,
    )
    with pytest.raises(ValidationError, match="current source/frame"):
        session.bind_ground_truth(wrong)

    truth = GroundTruth(
        np.zeros((8, 8), np.uint8), (tmp_path / "truth.png").resolve(),
        "b" * 64, "c" * 64, 0, False, first.session_id, first.source_sha256, 0,
    )
    session.bind_ground_truth(truth)
    second = InputMedia(
        first.source_path, first.source_sha256, "AVI", rgb, "video",
        first.session_id, 1, "fixture",
    )
    advanced = process_source(
        second, session.thresholds, 2,
        analysis_settings=session.analysis_settings,
        watershed_settings=session.watershed_settings,
        evaluation_target=session.evaluation_target,
        settings_revision=session.settings_revision,
    )
    assert session.commit_frame_result(advanced)
    assert session.ground_truth is None and session.result.evaluation is None
