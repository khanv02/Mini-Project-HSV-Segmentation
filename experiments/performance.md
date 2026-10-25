# Full-HD threshold-update performance

## Result

The retained 2026-10-25 measurement passed SC-003: **100 of 100** sequential valid
threshold changes presented their matching result within one second. Median latency was
557.28 ms, p95 was 638.01 ms, and maximum latency was 903.43 ms (minimum 447.39 ms).

The demonstration environment was Windows 10 build 26200 on an Intel64 Family 6 Model 151
Stepping 2 processor, CPython 3.11.9, Tcl/Tk 8.6. Package versions are retained in
`environment.json` and `uv.lock`.

## Input and procedure

`benchmark_performance.py` deterministically creates
`performance_input_1920x1080.png` (1920x1080 RGB, SHA-256
`723f977d11740c7086725a5272ed8f895db33ee6c14a0e37f764839798d69edc`). It then launches
the real Tk application controller at 1280x720 and opens that image through the normal
background worker.

For each of 100 distinct valid six-bound settings, the harness changes the visible Tk
variables and starts timing immediately before the final field edit. One matching result is
allowed to finish before the next edit. Timing includes the 75 ms control debounce, controller
submission, serialized worker processing, 25 ms completion polling, updates of all three
`ImageView` widgets, and Tk idle rendering. After each measured presentation, the retained mask
and segmented RGB are compared exactly with a fresh pure-processing result; this verification
work occurs after the timing endpoint. All 100 comparisons passed. The final controls were
H 153..183 degrees, S 42..96%, and V 36..100%, and the final output matched those controls.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe experiments\benchmark_performance.py
```

Machine-readable individual timings and metadata are retained in
`performance_results.json`. The earlier pre-optimization run achieved only 13/100 with a
1,399.77 ms median. The accepted run reuses the immutable source's HSV representation while
only thresholds change and avoids rebuilding the unchanged Original preview. Cache identity
includes both session and video frame, so source replacement or frame advancement recomputes HSV.

