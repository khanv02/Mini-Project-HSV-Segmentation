# Quickstart and Validation: HSV Color Segmentation

**Stage guide, 2026-10-24**: Phase 1 prepares the package skeleton and dependency lock.
The desktop application and algorithm test suite are not implemented at this milestone.
Setup checks are recorded in docs/verification.md. Application scenarios below apply to
later phases and are not claims of executed functional tests or measured performance.

## Prerequisites

- Windows 10/11 x64, CPython 3.11 x64 including Tcl/Tk, and permission to create local files.
- An implementation checkout containing pyproject.toml, requirements-lock.txt and package source.
- Internet or a prepared wheel cache for initial installation only. The running application
  and its image/video/experiment workflows must work without network services.
- PNG/JPEG/BMP samples and known decodable short MP4/AVI fixtures, with recorded encoding/backend.
- At least 10 experiment images with provenance and one real scene under two lighting conditions.

## Setup (PowerShell from Repository Root)

Check the intended interpreter; do not assume `python` from PATH is the Windows CPython build.

```powershell
py -3.11 --version
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m tkinter
```

The lock must include compatible runtime, test and build dependencies before using these
commands. Close the Tk demonstration window after confirming Tk is available. A normal package
installation in a second clean environment must also be verified before academic submission;
do not rely solely on an editable checkout. Record exact interpreter/Tcl/Tk/dependency versions.

## Automated Checks

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit -q
.\.venv\Scripts\python.exe -m pytest tests/integration -q
```

The first command must complete without creating a GUI or reading image files. It covers each
core function, errors, conversion tolerances and exact interval/mask/extraction behavior.
Integration checks use temporary files and deterministic frame/session doubles; real video
fixtures verify selected backend support. Experiment replay checks run once the documented
experiment collection exists; missing evidence must not be reported as a successful replay.

## Launch and Image MVP

```powershell
.\.venv\Scripts\python.exe -m hsv_segmentation
```

1. Confirm the title and distinct file, threshold and visualization sections.
2. Open PNG, JPEG and BMP samples. Check three labeled views and unchanged aspect ratios.
3. Confirm defaults (H 0..360, S 0..100, V 0..100) select the whole image, including near-red
   pixels whose hue exceeds 359 degrees. Only the upper H control permits 360.
4. Change each of six values. Verify automatic updates without reopening input.
5. Test wrapped H (350,10), exact/equal bounds, empty selection and full selection.
6. Enter malformed/out-of-range or reversed S/V values. Verify specific feedback and no export
   of a result mislabeled with those values. Rapid valid edits must end at the final settings.

Expected numeric behavior is defined in [processing contract](contracts/processing.md), rather
than inferred only from appearance. Use its analytical cases for pixel-level acceptance.

## Video and Export

1. Open the known MP4/AVI fixture; verify first frame opens paused at index 0.
2. Play/pause, change thresholds while paused, continue to known EOF, then restart.
3. Verify source/mask/result frame identity throughout; open another input during playback.
4. Save mask and result for an image and a video frame. Reopen PNGs: dimensions match the source,
   mask has only 0/255, selected RGB values are unchanged, and excluded pixels are black.
5. Decline overwrite, cancel dialogs and try an unwritable destination; current state survives.
6. Try empty/corrupt/unsupported video; explicit or ambiguous decoder termination follows the
   messages in [desktop workflow](contracts/desktop-workflow.md), without false EOF certainty.

## Error Recovery and Responsiveness

Use a valid session before trying missing/unreadable/corrupt files, unsupported modes, invalid
bounds, Pillow safeguard failures, over-limit dimensions and simulated allocation/write errors.
After each recoverable error, complete another valid operation without restarting. Close while
work is pending and verify captures/work are released and no stale callbacks update Tk.

Record 100 distinct valid edit events on the documented demonstration computer using a
1920x1080 still image. Measure from the final edit event to presentation of its matching result,
including debounce and rendering. Allow one result to render before the next measured edit;
measure rapid-edit coalescing separately. At least 95 of 100 timings must be <=1 second.
Report hardware/software, input, six-bound sequence, individual timings and counting method
in experiments/performance.md. Synthetic scheduling tests alone do not establish real latency.

## Ten-Image Evaluation and Acceptance

1. Record a source manifest and environment per [record contract](contracts/experiment-record.md).
2. For each of at least 10 images, apply two different threshold sets, enter lighting and
   qualitative observations, then Record Experiment. Obtain at least 20 complete run directories.
3. Compare original/mask/result for every image: missed targets, unwanted regions and lighting
   effects. Save labeled comparisons in experiments/report.md; do not invent numerical accuracy.
4. Automatically replay three runs with exact decoded-pixel comparison and source hash checking.
5. Prepare quickstart/demo materials before arranging independent acceptance.
6. Have a second student replay three chosen runs and record genuine outcomes/date/issues.
7. Have a student follow opening/editing/comparing/saving instructions within five minutes,
   without instructor intervention. Record the actual time; an unavailable participant stays pending.
8. Verify all workflows with network services unavailable and Image Restoration absent.

Record evidence and unresolved failures in docs/verification.md and experiments/reproduction.md.
Final submission requires the independent checks; their absence must not be disguised as a pass.
