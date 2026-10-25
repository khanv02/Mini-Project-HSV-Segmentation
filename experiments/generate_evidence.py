"""Generate the Phase 7 manifest, environment record, 20 runs, and report.

Run from the repository root with the locked environment. The command refuses
to add evidence to a nonempty runs directory so an existing run is never
silently replaced.
"""

from __future__ import annotations

from importlib.metadata import version
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
import tkinter

import cv2

from hsv_segmentation.application.session import process_source
from hsv_segmentation.io.experiments import publish_experiment
from hsv_segmentation.io.images import load_image
from hsv_segmentation.models import HSVThresholdSet


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "experiments"
INPUTS = EXPERIMENTS / "inputs"
RUNS = EXPERIMENTS / "runs"

CASES = [
    ("simplecube_train_00_0002_natural.jpg", "outdoor skate-park scene", "green", (55, 175, 12, 100, 12, 100), (70, 145, 25, 100, 20, 90)),
    ("simplecube_train_00_0024_natural_shadow.jpg", "outdoor wooden-sign scene", "brown", (5, 55, 15, 100, 10, 90), (12, 42, 28, 100, 16, 72)),
    ("simplecube_train_03_9168_natural_indoor.jpg", "indoor shelf-and-globe scene", "red", (335, 30, 25, 100, 15, 100), (348, 16, 48, 100, 25, 88)),
    ("simplecube_train_16_1473_natural.jpg", "outdoor blue-telephone scene", "blue", (175, 260, 20, 100, 12, 100), (195, 235, 45, 100, 20, 88)),
    ("simplecube_train_00_0450_artificial.jpg", "indoor writing-board scene", "green", (65, 175, 18, 100, 12, 100), (85, 150, 42, 100, 20, 90)),
    ("simplecube_train_01_7977_artificial_night.jpg", "night street scene", "orange", (2, 62, 18, 100, 10, 100), (12, 42, 42, 100, 20, 88)),
    ("simplecube_train_02_8132_mixed.jpg", "indoor electrical-panel scene", "green", (55, 150, 15, 100, 12, 100), (70, 125, 35, 100, 20, 88)),
    ("simplecube_train_12_0361_mixed.jpg", "outdoor shopping-street scene", "blue", (175, 270, 20, 100, 12, 100), (195, 245, 42, 100, 20, 90)),
    ("mit_main_experiment120_dir00.jpg", "fixed hair-and-spheres scene", "blond hair", (18, 78, 8, 100, 12, 100), (28, 62, 18, 82, 22, 95)),
    ("mit_main_experiment120_dir24.jpg", "fixed hair-and-spheres scene", "blond hair", (18, 78, 8, 100, 12, 100), (28, 62, 18, 82, 22, 95)),
]

SIMPLECUBE_SOURCE = {
    "simplecube_train_00_0002_natural.jpg": "train_00_0002.jpg",
    "simplecube_train_00_0024_natural_shadow.jpg": "train_00_0024.jpg",
    "simplecube_train_03_9168_natural_indoor.jpg": "train_03_9168.jpg",
    "simplecube_train_16_1473_natural.jpg": "train_16_1473.jpg",
    "simplecube_train_00_0450_artificial.jpg": "train_00_0450.jpg",
    "simplecube_train_01_7977_artificial_night.jpg": "train_01_7977.jpg",
    "simplecube_train_02_8132_mixed.jpg": "train_02_8132.jpg",
    "simplecube_train_12_0361_mixed.jpg": "train_12_0361.jpg",
}

SIMPLECUBE_LIGHTING = {
    "simplecube_train_00_0002_natural.jpg": "Natural daylight, outdoor; no shadows annotated.",
    "simplecube_train_00_0024_natural_shadow.jpg": "Natural daylight, outdoor; shadows annotated.",
    "simplecube_train_03_9168_natural_indoor.jpg": "Natural illumination, indoor; shadows annotated.",
    "simplecube_train_16_1473_natural.jpg": "Natural daylight, outdoor; shadows annotated.",
    "simplecube_train_00_0450_artificial.jpg": "Artificial illumination, indoor; shadows annotated.",
    "simplecube_train_01_7977_artificial_night.jpg": "Artificial illumination, outdoor at night; shadows annotated.",
    "simplecube_train_02_8132_mixed.jpg": "Mixed illumination, indoor; shadows annotated.",
    "simplecube_train_12_0361_mixed.jpg": "Mixed illumination, outdoor in daytime; shadows annotated.",
}


def case_metadata(name: str, scene: str) -> dict[str, str]:
    if name.startswith("mit_"):
        direction = "0" if "dir00" in name else "24"
        return {
            "kind": "real photographed multi-illumination image",
            "scene_id": "MIT-main_experiment120",
            "scene": scene,
            "lighting": f"Controlled real directional light {direction} of 25; fixed camera and scene.",
            "provenance": (
                "MIT CSAIL Multi-Illumination Dataset scene main_experiment120, "
                f"dir_{direction}_mip5.jpg; copied without pixel edits."
            ),
            "permission": "CC-BY; attribution to Murmann, Gharbi, Aittala, and Durand (ICCV 2019).",
        }
    source_name = SIMPLECUBE_SOURCE[name]
    return {
        "kind": "real photographed color-constancy dataset image",
        "scene_id": f"SimpleCube++-{source_name.removesuffix('.jpg')}",
        "scene": scene,
        "lighting": SIMPLECUBE_LIGHTING[name],
        "provenance": (
            f"SimpleCube++ auxiliary/JPG/{source_name}; copied without pixel edits from the "
            "official Cube++ CC BY 4.0 dataset."
        ),
        "permission": "CC BY 4.0; attribution to the Cube++ dataset authors is required.",
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment_record() -> dict:
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True
        ).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, check=True
        ).stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = "unavailable", None
    return {
        "schema_version": 1,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "not reported by platform API",
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "tcl": str(tkinter.TclVersion),
        "tk": str(tkinter.TkVersion),
        "packages": {
            name: version(name)
            for name in ("numpy", "Pillow", "opencv-python", "pytest")
        },
        "opencv": cv2.__version__,
        "video_backend": "OpenCV FFMPEG (enabled in the locked Windows build)",
        "application_revision": revision,
        "working_tree_dirty": dirty,
        "generation_command": ".\\.venv\\Scripts\\python.exe experiments\\generate_evidence.py",
    }


def thresholds(values: tuple[int, ...], revision: int) -> HSVThresholdSet:
    return HSVThresholdSet(*values, parameter_revision=revision)


def main() -> None:
    missing = [name for name, *_ in CASES if not (INPUTS / name).is_file()]
    if missing:
        raise SystemExit(f"Missing experiment inputs: {', '.join(missing)}")
    RUNS.mkdir(parents=True, exist_ok=True)
    if any(RUNS.iterdir()):
        raise SystemExit("experiments/runs must be empty; existing evidence was preserved")

    environment_path = EXPERIMENTS / "environment.json"
    environment_path.write_text(
        json.dumps(environment_record(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "criteria": {
            "minimum_distinct_images": 10,
            "runs_per_image": 2,
            "photographed_same_scene_two_real_lighting_conditions": {
                "status": "verified",
                "scene_id": "MIT-main_experiment120",
                "input_paths": [
                    "inputs/mit_main_experiment120_dir00.jpg",
                    "inputs/mit_main_experiment120_dir24.jpg",
                ],
                "lighting_conditions": ["direction 0 of 25", "direction 24 of 25"],
                "evidence": "MIT dataset definition fixes the real photographed scene and camera while changing the active directional light.",
            },
        },
        "inputs": [],
    }
    report_rows = []
    for index, (name, scene, target, broad, narrow) in enumerate(CASES, start=1):
        path = (INPUTS / name).resolve()
        source = load_image(path)
        metadata = case_metadata(name, scene)
        entry = {
            "id": f"IMG-{index:03d}",
            "path": f"inputs/{name}",
            "sha256": sha256(path),
            "width": source.width,
            "height": source.height,
            **metadata,
            "runs": [],
        }
        for setting_index, (label, values) in enumerate((("broad", broad), ("narrow", narrow)), start=1):
            setting = thresholds(values, setting_index)
            snapshot = process_source(source, setting, setting_index)
            selected = float((snapshot.mask == 255).mean() * 100.0)
            if label == "broad":
                observation = (
                    f"Broad {target} interval selected {selected:.2f}% of pixels; it retains more shaded target colors "
                    "but may include similarly colored background regions. No ground-truth accuracy is claimed."
                )
            else:
                observation = (
                    f"Narrow {target} interval selected {selected:.2f}% of pixels; it reduces unwanted colors "
                    "but may miss darker or less saturated target regions. No ground-truth accuracy is claimed."
                )
            receipt = publish_experiment(
                snapshot,
                lighting=entry["lighting"],
                observations=observation,
                runs_dir=RUNS,
                environment_path=environment_path,
            )
            entry["runs"].append({
                "setting": label,
                "thresholds": setting.as_dict(),
                "run_id": str(receipt.run_id),
                "record": f"runs/{receipt.run_id}/record.json",
            })
            relative_source = f"inputs/{name}"
            relative_run = f"runs/{receipt.run_id}"
            report_rows.append(
                f"| {entry['id']} / {label} | ![original]({relative_source}) | "
                f"![mask]({relative_run}/mask.png) | ![result]({relative_run}/result.png) | {observation} |"
            )
        manifest["inputs"].append(entry)

    (EXPERIMENTS / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    report = """# HSV experiment comparisons

Generated from the immutable records in `experiments/runs/`. Each row links the source,
binary mask, and segmented RGB output at source resolution. Selection percentages describe
mask coverage only; they are not accuracy measurements because no ground-truth labels exist.

The broad setting favors target recall and can admit similarly colored background. The narrow
setting favors color specificity and can miss shaded/desaturated target pixels. IMG-009 and
IMG-010 are the same real photographed scene under directional lights 0 and 24, providing a
controlled view of lighting-dependent HSV selection without treating synthetic edits as evidence.

| Input / setting | Original | Binary mask | Segmented result | Observation |
|---|---|---|---|---|
""" + "\n".join(report_rows) + "\n"
    (EXPERIMENTS / "report.md").write_text(report, encoding="utf-8")
    print(f"Published {len(report_rows)} runs for {len(CASES)} distinct images.")


if __name__ == "__main__":
    main()
