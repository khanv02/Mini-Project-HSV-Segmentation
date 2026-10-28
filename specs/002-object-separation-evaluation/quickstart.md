# Quickstart Validation Guide

This is the repeatable acceptance procedure for the implemented feature. Actual recorded
evidence is in `docs/verification.md` and `experiments/feature-002/report.md`.
Use a Windows machine with supported Python/Tcl/Tk and locally decodable test videos.

```powershell
uv sync --locked --extra test
uv run --locked --extra test pytest -q
uv run --locked hsv
```

Run the focused feature suites with:

```powershell
uv run --locked --extra test pytest tests/unit/test_object_analysis.py tests/unit/test_watershed.py tests/unit/test_evaluation.py -q
uv run --locked --extra test pytest tests/integration/test_ground_truth.py tests/integration/test_analysis_session.py tests/integration/test_analysis_ui.py tests/integration/test_extended_experiments.py -q
```

1. D1: generate fixtures using the future `tests/fixtures/analysis_cases.py` helpers; open the
   rectangles/noise case, enable analysis, compare known areas/centroids/boxes, vary minimum
   area and connectivity, toggle annotations and test zoom/ROI sampling alignment.
2. D2: open touching disks with documented two-seed settings, enable Watershed, inspect two
   labels and clipped boundaries. Test empty/no-marker cases, then disable and compare baseline
   pixels. Do not interpret this fixture as proof of separation for all images.
3. D3: load generated truth for partial overlap; verify IoU=0.5 and Dice=2/3 with TP=2,
   FP=1,FN=1. Exercise both-empty/one-empty, RGB rejection, size mismatch and cancel.
4. D4: pause a short supported video, load frame-specific truth, change thresholds, then
   advance/restart and verify truth/metrics clear. Delay jobs to verify stale-result rejection.
5. D5: save baseline PNGs and extended experiments. Verify hashes and replay against
   contracts/experiment-record.md; run existing legacy replay tests without modifying old runs.
6. At 960x640 and large desktop, show/hide histogram and new panel, check preview areas,
   focus order and all original workflows. Record screenshots and actual manual outcomes.
7. Run `scripts/benchmark_gui_performance.py` for baseline and extend its measurement options
   per tasks for analysis/Watershed heartbeat/memory evidence. Write new evidence to a separate
   feature-002 destination; never overwrite retained baseline measurements or experiment runs.

Record commands, environment, fixture hashes, actual counts/scores/timing and pass/fail/skipped
status in the future feature-002 section of `docs/verification.md`. Missing codec/human evidence
remains pending. Existing feature-001 human acceptance is not completed by these automated checks.
