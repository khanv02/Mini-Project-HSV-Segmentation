"""Replay retained experiment evidence from source identity and thresholds."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from hsv_segmentation.application.session import process_source
from hsv_segmentation.io.experiments import pixel_sha256
from hsv_segmentation.io.images import load_image
from hsv_segmentation.models import HSVThresholdSet


ROOT = Path(__file__).resolve().parents[2]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_manifest_has_ten_distinct_inputs_and_two_complete_runs_each() -> None:
    manifest = json.loads((ROOT / "experiments/manifest.json").read_text(encoding="utf-8"))
    inputs = manifest["inputs"]
    assert len(inputs) >= 10
    assert len({item["sha256"] for item in inputs}) == len(inputs)
    for item in inputs:
        source = ROOT / "experiments" / item["path"]
        assert source.is_file() and _sha(source) == item["sha256"]
        assert item["provenance"] and item["permission"] and item["lighting"]
        assert len(item["runs"]) >= 2
        assert item["runs"][0]["thresholds"] != item["runs"][1]["thresholds"]
        for run in item["runs"]:
            record = ROOT / "experiments" / run["record"]
            assert record.is_file()
            run_dir = record.parent
            assert (run_dir / "mask.png").is_file()
            assert (run_dir / "result.png").is_file()

    lighting_pair = manifest["criteria"][
        "photographed_same_scene_two_real_lighting_conditions"
    ]
    assert lighting_pair["status"] == "verified"
    pair = [
        next(item for item in inputs if item["path"] == path)
        for path in lighting_pair["input_paths"]
    ]
    assert pair[0]["scene_id"] == pair[1]["scene_id"] == lighting_pair["scene_id"]
    assert pair[0]["lighting"] != pair[1]["lighting"]
    assert all("CC-BY" in item["permission"] for item in pair)


def test_three_recorded_runs_reproduce_exact_decoded_pixels() -> None:
    manifest = json.loads((ROOT / "experiments/manifest.json").read_text(encoding="utf-8"))
    selected = [(item, item["runs"][0]) for item in manifest["inputs"][:3]]
    for item, run in selected:
        record_path = ROOT / "experiments" / run["record"]
        record = json.loads(record_path.read_text(encoding="utf-8"))
        run_dir = record_path.parent
        source_path = (run_dir / record["source"]["path"]).resolve()
        environment_path = (run_dir / record["environment"]["path"]).resolve()
        assert _sha(source_path) == record["source"]["sha256"] == item["sha256"]
        assert _sha(environment_path) == record["environment"]["sha256"]

        source = load_image(source_path)
        snapshot = process_source(source, HSVThresholdSet(**record["thresholds"]), 0)
        decoded_mask = np.asarray(Image.open(run_dir / "mask.png"))
        decoded_result = np.asarray(Image.open(run_dir / "result.png").convert("RGB"))
        np.testing.assert_array_equal(decoded_mask, snapshot.mask)
        np.testing.assert_array_equal(decoded_result, snapshot.segmented_rgb)
        assert pixel_sha256(decoded_mask) == record["artifacts"]["mask"]["pixel_sha256"]
        assert pixel_sha256(decoded_result) == record["artifacts"]["result"]["pixel_sha256"]
