"""Integrity and decoder smoke checks for the published FMT-001..FMT-007 set."""

from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from hsv_segmentation.io.images import load_image
from hsv_segmentation.io.video import VideoReader


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPOSITORY_ROOT / "tests" / "fixtures" / "acceptance_media" / "manifest.json"


def test_published_format_inventory_has_stable_files_hashes_and_decoders() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    cases = manifest["cases"]
    assert [case["case_id"] for case in cases] == [f"FMT-{index:03d}" for index in range(1, 8)]

    for case in cases:
        path = REPOSITORY_ROOT / case["path"]
        assert path.is_file()
        assert sha256(path.read_bytes()).hexdigest() == case["sha256"]
        if case["case_id"] <= "FMT-005":
            media = load_image(path)
            assert media.rgb.dtype == np.uint8
            assert media.rgb.shape == (case["height"], case["width"], 3)
        else:
            reader = VideoReader.open(path, trust_frame_count=True)
            try:
                assert reader.backend == case["backend"]
                assert reader.frame_count_hint == case["reported_frame_count"] == 3
                assert (reader.first_frame.width, reader.first_frame.height) == (
                    case["width"], case["height"]
                )
            finally:
                reader.release()
