import json
from pathlib import Path

import numpy as np
import pytest

from hsv_segmentation.application.session import process_source
from hsv_segmentation.io.experiments import label_sha256, publish_experiment
from hsv_segmentation.models import (
    AnalysisSettings, GroundTruth, HSVThresholdSet, InputMedia, WatershedSettings,
)
from scripts.generate_experiment_evidence import load_versioned_record


def media(tmp_path: Path, rgb: np.ndarray) -> InputMedia:
    path = (tmp_path / "source.png").resolve(); path.write_bytes(b"source")
    return InputMedia(path, "a" * 64, "PNG", rgb)


def test_baseline_stays_schema_one_and_extended_run_is_reproducible(tmp_path) -> None:
    rgb = np.zeros((12, 12, 3), np.uint8); rgb[2:5, 2:5] = (255, 0, 0)
    source = media(tmp_path, rgb)
    environment = tmp_path / "environment.json"; environment.write_text("{}", encoding="utf-8")
    baseline = process_source(source, HSVThresholdSet(), 1)
    receipt = publish_experiment(baseline, "lab", "baseline", tmp_path / "runs", environment)
    assert json.loads(receipt.record_path.read_text())["schema_version"] == 1

    truth_mask = baseline.mask.copy()
    truth = GroundTruth(
        truth_mask, (tmp_path / "truth.png").resolve(), "b" * 64, "c" * 64,
        0, False, source.session_id, source.source_sha256, None, 1,
    )
    extended = process_source(
        source, HSVThresholdSet(), 2,
        analysis_settings=AnalysisSettings(True, 8, 1),
        watershed_settings=WatershedSettings(False), ground_truth=truth,
    )
    receipt = publish_experiment(extended, "lab", "evaluated", tmp_path / "runs", environment)
    record = json.loads(receipt.record_path.read_text())
    assert record["schema_version"] == 2
    assert record["analysis"]["retained_count"] == 1
    assert record["evaluation"]["iou"] == 1
    assert (receipt.run_dir / "components_mask.png").is_file()
    assert (receipt.run_dir / "ground_truth.png").is_file()
    assert load_versioned_record(receipt.record_path)["schema_version"] == 2


def test_label_hash_is_shape_and_value_sensitive() -> None:
    labels = np.array([[0, 1], [2, 2]], np.int32)
    assert label_sha256(labels) == label_sha256(labels.copy())
    changed = labels.copy(); changed[0, 0] = 1
    assert label_sha256(labels) != label_sha256(changed)


def test_unknown_record_version_is_rejected(tmp_path) -> None:
    path = tmp_path / "record.json"; path.write_text('{"schema_version": 99}', encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported"):
        load_versioned_record(path)
