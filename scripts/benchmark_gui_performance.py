"""Measure 100 complete 1920x1080 GUI threshold updates on Windows/Tk."""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from hashlib import sha256
import json
import os
import platform
from pathlib import Path
from time import perf_counter, sleep
import tkinter as tk

import numpy as np
from PIL import Image

from hsv_segmentation.gui.controller import ApplicationController
from hsv_segmentation.models import (
    AnalysisSettings, GrayscaleSettings, HSVThresholdSet, THRESHOLD_FIELDS,
    WatershedSettings,
)
from hsv_segmentation.processing.segmentation import segment


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "experiments" / "performance_input_1920x1080.png"
DEFAULT_OUTPUT = ROOT / "experiments" / "performance_results.json"


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def process_peak_working_set() -> int | None:
    """Read the Windows process peak without instrumenting Python allocations."""
    if os.name != "nt":
        return None
    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    get_process = ctypes.windll.kernel32.GetCurrentProcess
    get_process.restype = wintypes.HANDLE
    get_memory = ctypes.windll.psapi.GetProcessMemoryInfo
    get_memory.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(_ProcessMemoryCounters), wintypes.DWORD,
    )
    get_memory.restype = wintypes.BOOL
    process = get_process()
    ok = get_memory(
        process, ctypes.byref(counters), counters.cb
    )
    return int(counters.PeakWorkingSetSize) if ok else None


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


def run(input_path: Path, output_path: Path, mode: str = "baseline") -> dict[str, object]:
    if mode not in {"baseline", "analysis", "watershed", "grayscale-full-hd"}:
        raise ValueError("unsupported benchmark mode")
    create_input(input_path)
    if mode == "grayscale-full-hd":
        rgb = np.asarray(Image.open(input_path).convert("RGB"))
        gray = np.repeat(rgb[..., :1], 3, axis=2)
        Image.fromarray(gray).save(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    input_hash = sha256(input_path.read_bytes()).hexdigest()

    root = tk.Tk()
    root.geometry("960x640")
    root.update()
    controller = ApplicationController(root)
    timings_ms: list[float] = []
    heartbeat_ms: list[float] = []
    heartbeat_during_pending: list[bool] = []
    benchmark_min_area = 512
    try:
        controller.open_image_path(str(input_path))
        pump_until(root, lambda: controller.session.result is not None, 30.0)
        if mode == "grayscale-full-hd":
            controller._on_segmentation_mode("grayscale")
            pump_until(root, lambda: controller.session.result.segmentation_mode == "grayscale", 30.0)
        if mode == "analysis":
            controller._on_analysis_settings(
                AnalysisSettings(True, 8, benchmark_min_area),
                WatershedSettings(False), "components"
            )
            pump_until(root, lambda: controller.session.result.analysis is not None, 30.0)
        elif mode == "watershed":
            controller._on_analysis_settings(
                AnalysisSettings(True, 8, benchmark_min_area),
                WatershedSettings(True, 0.7, 1, 3),
                "watershed",
            )
            pump_until(root, lambda: controller.session.result.watershed is not None, 30.0)
        root.update()

        for index in range(100):
            if mode == "grayscale-full-hd":
                threshold = (index * 17) % 256
                started = perf_counter()
                controller._on_grayscale_settings(GrayscaleSettings(
                    manual_threshold=threshold, settings_revision=index + 1
                ))
                pump_until(root, lambda: controller.worker.is_busy, 5.0)
                heartbeat_started = perf_counter()
                heartbeat: dict[str, float | bool] = {}
                root.after(0, lambda begun=heartbeat_started: heartbeat.update(
                    delay_ms=(perf_counter() - begun) * 1000.0,
                    during_pending=controller.worker.is_busy,
                ))
                pump_until(root, lambda value=threshold: (
                    controller.session.result.grayscale_settings.manual_threshold == value
                ), 30.0)
                elapsed_ms = (perf_counter() - started) * 1000.0
                timings_ms.append(elapsed_ms)
                heartbeat_ms.append(float(heartbeat.get("delay_ms", elapsed_ms)))
                heartbeat_during_pending.append(bool(heartbeat.get("during_pending", False)))
                continue
            values = threshold_values(index)
            for name in THRESHOLD_FIELDS[:-1]:
                controller.controls.fields[name].set(str(values[name]))
            started = perf_counter()
            final_name = THRESHOLD_FIELDS[-1]
            controller.controls.fields[final_name].set(str(values[final_name]))

            # The 75 ms control debounce must submit real worker work before the
            # responsiveness sample begins. A callback that runs after the worker
            # has finished is retained for transparency but is not a pending sample.
            pump_until(root, lambda: controller.worker.is_busy, 5.0)
            heartbeat_started = perf_counter()
            heartbeat: dict[str, float | bool] = {}

            def record_heartbeat(begun=heartbeat_started) -> None:
                heartbeat["delay_ms"] = (perf_counter() - begun) * 1000.0
                heartbeat["during_pending"] = controller.worker.is_busy

            root.after(0, record_heartbeat)

            try:
                pump_until(
                    root,
                    lambda expected=values: (
                        controller.session.result is not None
                        and controller.session.result.thresholds.as_dict() == expected
                        and all(view.has_source for view in controller.window.views)
                    ),
                    30.0,
                )
            except TimeoutError as error:
                current = controller.session.result
                current_values = None if current is None else current.thresholds.as_dict()
                raise TimeoutError(
                    f"{error}; edit={index + 1}; current={current_values}; "
                    f"status={controller.window.status_var.get()}"
                ) from error
            elapsed_ms = (perf_counter() - started) * 1000.0
            timings_ms.append(elapsed_ms)
            heartbeat_ms.append(float(heartbeat.get("delay_ms", elapsed_ms)))
            heartbeat_during_pending.append(bool(heartbeat.get("during_pending", False)))

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
        peak_bytes = process_peak_working_set()
        controller.close()

    within_one_second = sum(value <= 1000.0 for value in timings_ms)
    pending_heartbeat_ms = [
        value for value, pending in zip(heartbeat_ms, heartbeat_during_pending) if pending
    ]
    heartbeat_pending_samples = len(pending_heartbeat_ms)
    heartbeat_within_limit = sum(value <= 250.0 for value in pending_heartbeat_ms)
    heartbeat_criterion_met = (
        heartbeat_pending_samples >= 95 and heartbeat_within_limit >= 95
    )
    latency_criterion_met = within_one_second >= 95 if mode in {"baseline", "grayscale-full-hd"} else None
    ordered = sorted(timings_ms)
    result_data: dict[str, object] = {
        "schema_version": 1,
        "mode": mode,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "tcl": str(tk.TclVersion),
        "tk": str(tk.TkVersion),
        "input": str(input_path.relative_to(ROOT)).replace("\\", "/"),
        "input_sha256": input_hash,
        "dimensions": [1920, 1080],
        "update_count": 100,
        "analysis_min_area_px": benchmark_min_area if mode != "baseline" else None,
        "within_one_second": within_one_second,
        "latency_criterion_met": latency_criterion_met,
        "criterion_met": (
            bool(latency_criterion_met) if mode == "baseline" else heartbeat_criterion_met
        ),
        "minimum_ms": min(timings_ms),
        "median_ms": ordered[len(ordered) // 2],
        "p95_ms": ordered[94],
        "maximum_ms": max(timings_ms),
        "heartbeat_scheduled_after_worker_start": True,
        "heartbeat_pending_samples": heartbeat_pending_samples,
        "heartbeat_within_250_ms": heartbeat_within_limit,
        "heartbeat_criterion_met": heartbeat_criterion_met,
        "peak_process_bytes": peak_bytes,
        "peak_memory_method": "Windows GetProcessMemoryInfo PeakWorkingSetSize",
        "heartbeat_ms": heartbeat_ms,
        "heartbeat_during_pending": heartbeat_during_pending,
        "timings_ms": timings_ms,
        "final_thresholds": threshold_values(99) if mode != "grayscale-full-hd" else {"intensity": (99 * 17) % 256},
        "final_output_exact": True,
        "measurement_scope": (
            "final Tk variable edit, 75 ms debounce, controller submission, serialized worker "
            "processing with cached source histogram, 25 ms polling, three ImageView updates, "
            "heartbeat scheduled only after worker busy state, 960x640 window, histogram hidden, "
            "and Tk idle rendering"
        ),
    }
    output_path.write_text(json.dumps(result_data, indent=2) + "\n", encoding="utf-8")
    return result_data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mode", choices=("baseline", "analysis", "watershed"), default="baseline")
    parser.add_argument("--scenario", choices=("grayscale-full-hd",), default=None)
    parser.add_argument("--iterations", type=int, default=100)
    args = parser.parse_args()
    if args.iterations != 100:
        parser.error("this acceptance benchmark requires exactly 100 iterations")
    result = run(args.input.resolve(), args.output.resolve(), args.scenario or args.mode)
    print(json.dumps({key: result[key] for key in (
        "mode", "within_one_second", "criterion_met", "heartbeat_within_250_ms",
        "heartbeat_criterion_met", "median_ms", "p95_ms", "maximum_ms"
    )}, indent=2))


if __name__ == "__main__":
    main()
