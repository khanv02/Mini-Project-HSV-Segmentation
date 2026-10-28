# Feature 002 Verification Report

Date: 2026-10-28  
Environment: Windows, CPython 3.11.16, Tcl/Tk 8.6, NumPy 2.4.6, OpenCV 4.14.0.94,
Pillow 12.3.0. All work is offline and uses the existing locked dependency families.

## Automated outcomes

- Full suite: 283 passed in 23.50 seconds; no skipped tests. One `.pytest_cache` ACL warning is unrelated to
  application behavior.
- D1: areas 1/4/9 produce raw count 3 and retained areas 4/9 at minimum 4. Connectivity,
  centroids, boxes, contours, empty/holed masks, immutability and stable IDs pass.
- D2: the 96x96 touching-disks fixture at seed fraction 0.7 produces two labels. Empty and
  one-seed inputs return explicit `empty`/`not_applied`; labels, union and ridges stay inside
  the HSV mask.
- D3: TP=2, FP=1, FN=1 gives IoU=0.5 and Dice=0.6666666666666666. Identical, disjoint,
  both-empty, one-empty and invalid mask cases pass. Lossless truth format/dimension failures
  preserve the prior state.
- D4: image/video source, frame, settings and truth revisions reject stale completions. Truth
  survives edits on one frame and clears on advancement/restart/replacement.
- D5: disabled extensions retain schema 1; extended snapshots publish schema 2 prediction,
  int32 labels and normalized truth with hashes. Existing records replay unchanged and unknown
  schema versions are rejected.

## Performance

Each file contains all 100 timings, all heartbeat timings, the input hash, final threshold
identity, platform, environment, and memory method. `minimum_area_px=512` is recorded for the
advanced Full-HD stress modes. The HSV output after every edit is compared exactly with fresh
pure segmentation. The histogram is hidden for this feature-002 responsiveness run; its visible
layout and prior visible-histogram performance remain covered by feature-001 evidence/tests.
The benchmark window uses the supported 960x640 minimum workspace while processing the complete
1920x1080 source arrays.

| Mode | <=1 second | Median | p95 | UI heartbeat <=250 ms | Acceptance |
| --- | ---: | ---: | ---: | ---: | --- |
| Baseline | 99/100 | 574.32 ms | 698.45 ms | 100/100 | PASS (requires >=95/100) |
| Analysis | 61/100 | 807.07 ms | 2909.04 ms | 100/100 | PASS responsiveness; no real-time latency guarantee |
| Watershed | 0/100 | 2957.78 ms | 9821.66 ms | 100/100 | PASS responsiveness; no real-time latency guarantee |

Peak process memory is measured using Windows `GetProcessMemoryInfo` / `PeakWorkingSetSize`,
which avoids instrumenting Python allocations inside the timed region. See
`performance-baseline.json`, `performance-analysis.json`, and `performance-watershed.json`.

## Requirement matrix

| Requirement | Evidence | Outcome |
| --- | --- | --- |
| FR-001, NFR-006 | Default-disabled full regression, legacy export/record tests | PASS |
| FR-002..004, SC-001 | Component, filter, visualization and D1 GUI tests | PASS |
| FR-005..006, SC-002 | Marker/Watershed unit tests, colored-region GUI display | PASS |
| FR-007 | Ground-truth format, threshold, hash and mismatch matrix | PASS |
| FR-008..010, SC-003 | Exact evaluation and confusion-overlay tests | PASS |
| FR-011..012, SC-004 | Image/video session and stale revision tests | PASS |
| FR-013, SC-005 | Schema 1/2 publication and replay tests | PASS |
| FR-014 | Typed adapter errors and normal not-applied status | PASS |
| NFR-001..002, NFR-005 | Offline pure modules, deterministic fixture suite | PASS |
| NFR-003 | Three-mode benchmark and heartbeat evidence | PASS |
| NFR-004 | 960x640 histogram/panel integration checks | PASS |
| SC-006 | Full regression, layout and benchmark evidence | PASS |

Manual visual inspection is supplementary and was not claimed. Existing feature-001 independent
student acceptance gates remain pending and are not changed by this implementation.
