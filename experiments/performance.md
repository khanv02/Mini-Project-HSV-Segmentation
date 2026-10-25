# Full-HD threshold-update performance

## Results

The retained Phase 9 measurement on 2026-10-25 passed SC-003 with the HSV histogram panel
visible: **99 of 100** sequential valid threshold changes presented their matching result within
one second. Median latency was 566.34 ms, p95 was 665.60 ms, and maximum latency was 1,413.79 ms
(minimum 501.04 ms). The single warm-up outlier exceeded one second; the required threshold is
at least 95/100.

The separate pre-histogram baseline, measured after the zoomable canvas refactor, achieved
**100 of 100**, with median 532.00 ms, p95 650.60 ms, maximum 884.83 ms and minimum 477.34 ms.
These baseline figures remain here for comparison and were not relabeled as a histogram run.

The measurement environment was Windows 10 build 26200 on an Intel64 Family 6 Model 151
Stepping 2 processor, CPython 3.11.16, Tcl/Tk 8.6. Exact timing metadata is retained in
`performance_results.json`; dependency versions are locked by `uv.lock`.

## Input and procedure

`scripts/benchmark_gui_performance.py` deterministically creates
`performance_input_1920x1080.png` (1920x1080 RGB, SHA-256
`723f977d11740c7086725a5272ed8f895db33ee6c14a0e37f764839798d69edc`). It then launches
the real Tk application controller at 1280x720, opens that image through the normal background
worker, and makes the HSV histogram panel visible before measurement.

For each of 100 distinct valid six-bound settings, the harness changes the visible Tk
variables and starts timing immediately before the final field edit. One matching result is
allowed to finish before the next edit. Timing includes the 75 ms control debounce, controller
submission, serialized worker processing, 25 ms completion polling, updates of all three
`ImageView` widgets and the cached histogram overlay, and Tk idle rendering. Histogram counts
are computed for the accepted source/frame and reused while only thresholds change. After each
measured presentation, the retained mask
and segmented RGB are compared exactly with a fresh pure-processing result; this verification
work occurs after the timing endpoint. All 100 comparisons passed. The final controls were
H 153..183 degrees, S 42..96%, and V 36..100%, and the final output matched those controls.

Run from the repository root:

```powershell
uv run python scripts/benchmark_gui_performance.py
```

Machine-readable individual timings and metadata are retained in
`performance_results.json`; that JSON contains the latest histogram-visible run. The earlier
pre-optimization run achieved only 13/100 with a 1,399.77 ms median. The accepted implementation
reuses the immutable source's HSV representation and histogram counts while only thresholds
change, and avoids rebuilding the unchanged Original preview. Cache identity includes session,
video frame and source hash, so source replacement or frame advancement recomputes both safely.

