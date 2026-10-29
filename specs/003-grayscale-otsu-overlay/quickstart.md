# Quickstart and Acceptance Guide

This is the implementation verification guide for Feature 003. Commands name the focused tests
that will be added by the task plan; run them as each story is completed.

## 1. Prepare the development environment

```powershell
uv sync --extra dev
```

Use deterministic generated fixtures in pytest temporary directories. Do not add ad-hoc sample
images to `experiments/inputs` as part of this feature unless they are intentionally documented
and reviewed experiment assets.

## 2. Verify manual grayscale segmentation (MVP)

```powershell
uv run pytest tests/unit/test_grayscale.py tests/integration/test_grayscale_session.py tests/integration/test_grayscale_ui.py -q
```

Manual demonstration:

1. Open a lossless image whose RGB channels are equal.
2. Confirm the app still starts in HSV mode.
3. Select Grayscale, Bright foreground and threshold `128`.
4. Confirm only intensities `129..255` are white in Binary Mask.
5. Select Dark and confirm intensities `0..128` are white.
6. Confirm Hue is marked unavailable and intensity remains visible.
7. Open a nearly-gray color fixture with one unequal channel and confirm Grayscale is rejected
   without replacing the HSV result.

## 3. Verify Otsu assistance

```powershell
uv run pytest tests/unit/test_grayscale.py -k otsu -q
uv run pytest tests/integration/test_grayscale_session.py tests/integration/test_playback.py -k otsu -q
```

Demonstrate a two-level eligible image, request Otsu and record the displayed threshold. Repeat to
confirm identical output. Then use a constant image and confirm the UI reports no meaningful split
while preserving the prior valid result. Return to Manual and confirm its editable value remains.

## 4. Verify Save Overlay

```powershell
uv run pytest tests/unit/test_visualization.py tests/unit/test_export.py tests/integration/test_export_session.py -q
```

For each Overlay variant—segmentation, object analysis, Watershed and TP/FP/FN—save a PNG, decode
it and compare its RGB array to the snapshot captured when export began. Confirm source dimensions,
cancel behavior, overwrite confirmation, unwritable destinations and a frame/display change during
the write. Save Mask and Save Result must remain byte/pixel-compatible with their prior tests.

## 5. Verify reproducible evidence

```powershell
uv run pytest tests/integration/test_extended_experiments.py tests/integration/test_experiment_reproduction.py -q
```

Record one manual grayscale run and one Otsu run. Verify schema 3 records mode, threshold source,
resolved threshold, polarity and hashes. Recompute both masks and any retained overlay. Replay
existing schema 1/2 HSV fixtures and confirm their interpretation is unchanged.

## 6. Run regression and performance acceptance

```powershell
uv run pytest -q
uv run python scripts/benchmark_gui_performance.py --scenario grayscale-full-hd --iterations 100
```

Retain benchmark output under the project's verification evidence convention. Acceptance requires
at least 95 of 100 current Full-HD grayscale edits within one second and all scheduled GUI
heartbeat checks within 250 ms while processing is pending.

## 7. Documentation review

The Vietnamese user documentation must let a first-time user complete the manual workflow in at
most three minutes and clearly explain:

- grayscale image versus binary mask;
- `> T` for Bright and `<= T` for Dark;
- why Otsu is global and may fail on constant/unevenly lit images;
- why visual quality is not an accuracy score without ground truth;
- the difference between Result and Overlay;
- where to find the focused feature and tutorial pages from the root README.
