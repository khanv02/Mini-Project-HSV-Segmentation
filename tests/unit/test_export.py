"""Lossless immutable Overlay export tests."""

import numpy as np
from PIL import Image

from hsv_segmentation.io.export import export_snapshot
from hsv_segmentation.models import OverlayDisplaySettings, OverlaySnapshot


def test_overlay_export_round_trips_exact_pixels(tmp_path):
    rgb = np.array([[[1, 2, 3], [250, 100, 0]]], dtype=np.uint8)
    snapshot = OverlaySnapshot(
        rgb, "segmentation", OverlayDisplaySettings(),
        (tmp_path / "source.png").resolve(), "a" * 64, "session", request_revision=4,
    )
    destination = (tmp_path / "overlay.png").resolve()
    receipt = export_snapshot(snapshot, "overlay", destination)
    np.testing.assert_array_equal(np.asarray(Image.open(destination).convert("RGB")), rgb)
    assert receipt.kind == "overlay"
    assert receipt.variant == "segmentation"
    assert receipt.session_id == "session"
