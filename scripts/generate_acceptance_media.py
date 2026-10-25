"""Generate the seven tiny, local supported-format acceptance fixtures."""

from hashlib import sha256
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


CASES = (
    ("FMT-001", "rgb.png", "8-bit RGB PNG"),
    ("FMT-002", "rgb.jpg", "8-bit RGB JPEG"),
    ("FMT-003", "rgb.bmp", "8-bit RGB BMP"),
    ("FMT-004", "grayscale.png", "8-bit grayscale PNG"),
    ("FMT-005", "rgba.png", "8-bit RGBA PNG"),
    ("FMT-006", "mjpg.avi", "AVI containing MJPG video"),
    ("FMT-007", "mp4v.mp4", "MP4 containing mp4v video"),
)


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_video(path: Path, codec: str, frames: list[np.ndarray]) -> None:
    height, width = frames[0].shape[:2]
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*codec), 5.0, (width, height)
    )
    if not writer.isOpened():
        raise RuntimeError(f"required {codec}/{path.suffix} writer is unavailable")
    try:
        for rgb in frames:
            writer.write(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    finally:
        writer.release()


def _probe_video(path: Path) -> dict[str, object]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError(f"generated video cannot be decoded: {path}")
    try:
        backend = capture.getBackendName()
        frame_count = int(round(capture.get(cv2.CAP_PROP_FRAME_COUNT)))
        width = int(round(capture.get(cv2.CAP_PROP_FRAME_WIDTH)))
        height = int(round(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        fourcc_value = int(round(capture.get(cv2.CAP_PROP_FOURCC)))
        fourcc = "".join(chr((fourcc_value >> (8 * index)) & 0xFF) for index in range(4))
        decoded = 0
        while True:
            ok, _frame = capture.read()
            if not ok:
                break
            decoded += 1
    finally:
        capture.release()
    if decoded != 3:
        raise RuntimeError(f"expected 3 decoded frames from {path}, got {decoded}")
    return {
        "backend": backend,
        "reported_fourcc": fourcc,
        "reported_frame_count": frame_count,
        "decoded_frame_count": decoded,
        "width": width,
        "height": height,
    }


def generate(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rgb = np.array(
        [
            [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 255]],
            [[0, 0, 0], [255, 255, 0], [0, 255, 255], [255, 0, 255]],
            [[32, 64, 96], [96, 64, 32], [10, 20, 30], [220, 180, 140]],
        ],
        dtype=np.uint8,
    )
    grayscale = np.array([[0, 64, 128, 255], [20, 80, 160, 220]], dtype=np.uint8)
    alpha = np.array([[0, 64, 128, 255], [255, 128, 64, 0], [20, 90, 180, 240]], dtype=np.uint8)
    rgba = np.dstack((rgb, alpha))
    Image.fromarray(rgb).save(output_dir / "rgb.png", format="PNG")
    Image.fromarray(rgb).save(
        output_dir / "rgb.jpg", format="JPEG", quality=95, subsampling=0, optimize=False
    )
    Image.fromarray(rgb).save(output_dir / "rgb.bmp", format="BMP")
    Image.fromarray(grayscale).save(output_dir / "grayscale.png", format="PNG")
    Image.fromarray(rgba).save(output_dir / "rgba.png", format="PNG")

    frames = [
        np.full((8, 10, 3), color, dtype=np.uint8)
        for color in ([220, 20, 20], [20, 220, 20], [20, 20, 220])
    ]
    _write_video(output_dir / "mjpg.avi", "MJPG", frames)
    _write_video(output_dir / "mp4v.mp4", "mp4v", frames)

    records = []
    for case_id, filename, representation in CASES:
        path = output_dir / filename
        record: dict[str, object] = {
            "case_id": case_id,
            "path": path.relative_to(output_dir.parents[2]).as_posix(),
            "representation": representation,
            "sha256": _digest(path),
            "provenance": "Generated from literal analytical arrays by scripts/generate_acceptance_media.py",
        }
        if path.suffix.lower() in {".avi", ".mp4"}:
            record.update(_probe_video(path))
        else:
            with Image.open(path) as image:
                record.update({"mode": image.mode, "width": image.width, "height": image.height})
        records.append(record)
    manifest = {
        "schema_version": 1,
        "generator": "scripts/generate_acceptance_media.py",
        "opencv_version": cv2.__version__,
        "cases": records,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[1]
    destination = repository_root / "tests" / "fixtures" / "acceptance_media"
    print(json.dumps(generate(destination), indent=2))
