"""Measure 100 complete 1920x1080 GUI threshold updates on Windows/Tk."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import platform
from pathlib import Path
from time import perf_counter, sleep
import tkinter as tk

import numpy as np
from PIL import Image

from hsv_segmentation.gui.controller import ApplicationController
from hsv_segmentation.models import HSVThresholdSet, THRESHOLD_FIELDS
from hsv_segmentation.processing.segmentation import segment


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "experiments" / "performance_input_1920x1080.png"
DEFAULT_OUTPUT = ROOT / "experiments" / "performance_results.json"


def create_input(path: Path) -> None:
    """Create a deterministic full-HD color field used only for timing."""
    x = np.arange(1920, dtype=np.uint16)[None, :]
    y = np.arange(1080, dtype=np.uint16)[:, None]
    rgb = np.empty((1080, 1920, 3), dtype=np.uint8)
    rgb[..., 0] = ((x + y) % 256).astype(np.uint8)
    rgb[..., 1] = ((2 * x + y) % 256).astype(np.uint8)
    rgb[..., 2] = ((x + 2 * y) % 256).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb, mode="RGB").save(path, format="PNG")


def pump_until(root: tk.Tk, predicate, timeout_seconds: float) -> None:
    deadline = perf_counter() + timeout_seconds
    while not predicate():
        root.update()
        if perf_counter() >= deadline:
            raise TimeoutError("GUI update did not complete before the benchmark timeout")
        sleep(0.001)
    root.update_idletasks()


def threshold_values(index: int) -> dict[str, int]:
    """Return 100 distinct valid settings; upper V changes on every final edit."""
    return {
        "lower_h_deg": (index * 7) % 180,
        "upper_h_deg": 180 + ((index * 11) % 181),
        "lower_s_pct": (index * 3) % 51,
        "upper_s_pct": 75 + (index % 26),
        "lower_v_pct": (index * 5) % 51,
        "upper_v_pct": 99 if index % 2 == 0 else 100,
    }


def run(input_path: Path, output_path: Path) -> dict[str, object]:
    create_input(input_path)
    input_hash = sha256(input_path.read_bytes()).hexdigest()

    root = tk.Tk()
    root.geometry("1280x720")
    root.update()
    controller = ApplicationController(root)
    timings_ms: list[float] = []
    try:
        controller.open_image_path(str(input_path))
        pump_until(root, lambda: controller.session.result is not None, 30.0)

        for index in range(100):
            values = threshold_values(index)
            for name in THRESHOLD_FIELDS[:-1]:
                controller.controls.fields[name].set(str(values[name]))
            started = perf_counter()
            final_name = THRESHOLD_FIELDS[-1]
            controller.controls.fields[final_name].set(str(values[final_name]))

            pump_until(
                root,
                lambda expected=values: (
                    controller.session.result is not None
                    and controller.session.result.thresholds.as_dict() == expected
                    and all(view.source_array is not None for view in controller.window.views)
                ),
                10.0,
            )
            elapsed_ms = (perf_counter() - started) * 1000.0
            timings_ms.append(elapsed_ms)

            result = controller.session.result
            assert result is not None
            expected_mask, expected_rgb = segment(
                result.source.rgb,
                HSVThresholdSet(**values),
            )
            if not np.array_equal(result.mask, expected_mask):
                raise AssertionError(f"mask mismatch after edit {index + 1}")
            if not np.array_equal(result.segmented_rgb, expected_rgb):
                raise AssertionError(f"result mismatch after edit {index + 1}")
    finally:
        controller.close()

    within_one_second = sum(value <= 1000.0 for value in timings_ms)
    ordered = sorted(timings_ms)
    result_data: dict[str, object] = {
        "schema_version": 1,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "tcl": str(tk.TclVersion),
        "tk": str(tk.TkVersion),
        "input": str(input_path.relative_to(ROOT)).replace("\\", "/"),
        "input_sha256": input_hash,
        "dimensions": [1920, 1080],
        "update_count": 100,
        "within_one_second": within_one_second,
        "criterion_met": within_one_second >= 95,
        "minimum_ms": min(timings_ms),
        "median_ms": ordered[len(ordered) // 2],
        "p95_ms": ordered[94],
        "maximum_ms": max(timings_ms),
        "timings_ms": timings_ms,
        "final_thresholds": threshold_values(99),
        "final_output_exact": True,
        "measurement_scope": (
            "final Tk variable edit, 75 ms debounce, controller submission, serialized worker "
            "processing, 25 ms polling, three ImageView updates, and Tk idle rendering"
        ),
    }
    output_path.write_text(json.dumps(result_data, indent=2) + "\n", encoding="utf-8")
    return result_data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.input.resolve(), args.output.resolve())
    print(json.dumps({key: result[key] for key in (
        "within_one_second", "criterion_met", "median_ms", "p95_ms", "maximum_ms"
    )}, indent=2))


if __name__ == "__main__":
    main()
