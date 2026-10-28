# Implementation Plan: HSV Object Analysis, Separation and Evaluation

**Branch**: Existing branch retained | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: `specs/002-object-separation-evaluation/spec.md`

## Summary

Extend verified HSV infrastructure with pure component/contour analysis, optional marker-based
Watershed, and ground-truth evaluation. Preserve baseline outputs and export behavior. Derived
analysis remains separate, revision-bound and reproducible. This document plans changes only.

## Technical Context

**Language/Version**: Python >=3.11; current local interpreter 3.14 (not target-validation evidence).

**Primary Dependencies**: Existing NumPy 2.x, OpenCV 4.x, Pillow 11/12 and standard-library Tkinter/ttk.

**Storage**: Local PNG/BMP inputs, PNG artifacts and versioned JSON experiment records.

**Testing**: Existing pytest unit/integration suites; analytical synthetic masks and real Tk checks.

**Target Platform**: Existing Windows desktop; retain existing codec-dependent MP4/AVI support.

**Project Type**: Single desktop application/package, no service or GUI rewrite.

**Performance Goals**: Spec NFR-003: baseline >=95/100 Full-HD updates <=1s; UI heartbeat
>=95/100 <=250ms during extension work; measure extension median/p95 and memory, no FPS promise.

**Constraints**: Offline; current 12,000,000-pixel input limit; no new dependencies;
960x640 layout and three previews; compatible positional constructors and baseline records.

**Scale/Scope**: One local session/current frame; optional analysis and one bound ground truth.

## Constitution Check

| Principles | Before research | After design | Design evidence |
| --- | --- | --- | --- |
| I, V, IX correctness/readability/documentation | PASS | PASS | Explicit coordinates, counts, marker/empty rules and demonstration evidence |
| II, III, XIII modularity/separation/architecture | PASS | PASS | Existing four layers retained; pure algorithms and dedicated truth I/O |
| IV, VIII simplicity/dependencies/scope | PASS | PASS | Existing OpenCV/NumPy; no services, tracking or GUI migration |
| VI, VII, XIV independent tests/acceptance | PASS | PASS | Per-story analytical, state, UI and replay tasks |
| X HSV core | PASS | PASS | New stages consume baseline; HSV conversion/selection unchanged |
| XI compatibility | PASS | PASS | Default-disabled fields; baseline exports/schema 1 retained |
| XII configuration | PASS | PASS | Validated settings with units/ranges/defaults, persisted in schema 2 |

These are design gates, not claims that implementation or runtime acceptance passed. No exception.

## Project Structure

### Documentation (this feature)

`specs/002-object-separation-evaluation/` contains spec, plan, research, data-model, quickstart,
tasks, `contracts/{processing,desktop-workflow,experiment-record}.md` and quality checklist.
Feature 001 remains unchanged as historical baseline, including its pending human acceptance.

### Source Code (repository root)

Existing paths verified in [research.md](research.md). Proposed additions are explicitly new:

```text
src/hsv_segmentation/
  models.py                          # extend settings and immutable optional results
  processing/
    object_analysis.py               # NEW components, contours and filtering
    watershed.py                     # NEW distance markers and constrained separation
    evaluation.py                    # NEW overlap counts and scores
    visualization.py                 # extend pure annotations/confusion composition
  io/
    ground_truth.py                  # NEW dedicated lossless truth decoding
    experiments.py                   # extend optional version-2 publication
  application/
    session.py                       # canonical processing orchestration/state
    processing_worker.py             # cache delegates to same processing path
    playback.py                      # pass settings through every video path
  gui/
    analysis_panel.py                # NEW focused settings/statistics/evaluation widget
    controller.py                    # revision/truth/events/record wiring
    main_window.py                   # compose panel and derived displays
tests/fixtures/analysis_cases.py      # NEW analytical masks
tests/unit/test_object_analysis.py    # NEW
tests/unit/test_watershed.py          # NEW
tests/unit/test_evaluation.py         # NEW
tests/integration/test_ground_truth.py       # NEW
tests/integration/test_analysis_session.py   # NEW
tests/integration/test_analysis_ui.py        # NEW
tests/integration/test_extended_experiments.py # NEW
```

**Structure Decision**: Keep existing package and imports GUI -> application -> processing/I/O;
shared models/errors do not depend on GUI. Proposed files address distinct concrete concerns.
Keep `ImageView` zoom/pan and source mapping intact; annotations are separate display arrays.
Do not expand `models.py` into a new package or add a registry/framework.

### Data Flow and Integration Points

1. Existing `load_image`/`VideoReader` -> immutable `InputMedia`.
2. `process_source` -> cached or computed float64 HSV/histogram -> `generate_mask` -> existing
   optional `apply_morphology` -> unchanged baseline mask/result.
3. When enabled: baseline -> component analysis/filtering; independently baseline + source ->
   Watershed labels. Minimum area applies to reported labels/derived prediction, not marker creation.
4. Explicit target + matching truth -> evaluation counts/scores; derived foreground excludes
   Watershed ridges. Analysis uses source-coordinate arrays, not resized previews.
5. One result snapshot -> revision-checked commit -> GUI presentation; worker never touches Tk.
6. Captured result/truth -> background publication of baseline plus optional extension evidence.

Remove duplicated orchestration between `process_source` and `_CachedProcessor`: the cached
processor retains HSV/histogram caching but delegates to `process_source(..., hsv=..., histogram=...)`.
This justified small refactor prevents new stages diverging across image/video paths.
Append defaulted optional request/result fields; leave `segment(rgb, thresholds)` returning its
existing pair. Add keyword-only optional arguments to existing public application callables.
Session/controller guards must compare request, settings and truth revisions, not only threshold
revision. Thread them through submit_image and PlaybackSession prepare_open/next/restart and
reprocess_current. Reject stale ground-truth-load completions using captured source/frame binding.

### Algorithm Design

- Components: `connectedComponentsWithStats` with explicit connectivity/int32 output; exclude
  label 0, use CC_STAT_AREA and centroids. Normalize retained IDs by first foreground pixel in
  row-major order for reproducibility. Build filtered mask with inclusive minimum-area test.
  Extract per-label external contours with `findContours(RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)`;
  all contours for a label remain associated with that label. Holes are excluded from object
  count and pixel area naturally reflects them. Bounding boxes come from component stats;
  no need to add redundant `boundingRect` calls.
- Watershed: validate source/mask/settings, pad mask with a one-pixel zero border for distance
  calculation, then crop distances. Use L2 distanceTransform and explicit mask size 5; foreground
  seed = distance > seed_fraction * max_distance. Expand baseline for background with configured
  odd kernel/iterations. Label seeds; markers: background=1, foreground>=2, unknown=0. Require
  >=2 foreground labels and some known background; tiny inputs or otherwise unusable markers
  return not-applied. Call watershed on contiguous source BGR copy and int32 marker copy.
  Restrict positive object labels and -1 boundaries to baseline foreground; normalize labels.
  Recompute area/centroid/boxes from separated labels without reconnecting ridge-adjacent regions.
  Filter by minimum area after splitting. Never run CC on the final union to recover instances.
- Evaluation: normalize truth in its I/O adapter; processing accepts only validated uint8
  0/255 masks of matching nonempty shape. Compute TP/FP/FN/TN with boolean operations and integer
  counts; use explicit both-empty denominator handling. RGB confusion composition is pure.

### GUI Modifications and Error Handling

Add a collapsible/tabbed analysis panel beside existing inspector/workspace, retaining theme
and keyboard traversal. Include analysis enable, 4/8 connectivity, minimum area, contour/box
toggles, region table, Watershed switch/settings/status, named target selector, Load/Clear Truth,
normalization threshold, scores and optional confusion legend. Do not replace baseline previews.
Provide an explicit derived comparison view selector and label what it shows; Save Mask/Result
continue exporting baseline. Extended experiments hold derived artifacts separately.

Use existing typed errors and recovery formatter. Catch cv2/resource errors at application
boundaries; parameter failure keeps last valid configuration. Insufficient seeds are data,
not exceptions. Loading truth pauses playback; cancellation preserves data and leaves video
paused with status. Do not silently reactivate truth after frame advancement or restart.
Pending/unavailable derived targets disable extended recording and show no numeric score.

### Testing Strategy and Performance

Use analytical masks with holes, diagonal contact, empty/full, border regions, noise and exact
area thresholds. Compare integer counts exactly, centroid/score values at 1e-12 tolerance.
Build touching disks with known two-seed settings; assert two labels and domain confinement,
not universal quality or version-independent watershed pixel layout. Test input immutability,
validation and execution without Tk/I/O. Cover threshold-only cached and uncached equality.
Integration checks inject delayed work to verify settings/truth changes, source replacement,
video pause/advance/restart, write failure and close. Add schema-1/2 replay and artifact hashes.

Cache HSV/histogram by current identity; do not cache analysis across different settings/truth.
Skip disabled stages and hidden confusion composition; keep bounded worker/coalescing. Count
regions using vectorized label lookup; avoid one full-frame copy per region where practical.
Record total latency, UI heartbeat delay and process peak memory; release distance/marker
temporaries after snapshot construction. Do not assume 12M-pixel limit guarantees enough RAM.
Run unchanged baseline benchmark separately and store new evidence without overwriting old runs.

### Phase 0: Research Decisions

Completed local source and installed-API inspection; see [research.md](research.md).

### Phase 1: Design and Contracts

See [data-model.md](data-model.md), [processing contract](contracts/processing.md),
[desktop workflow](contracts/desktop-workflow.md), [record contract](contracts/experiment-record.md)
and [quickstart.md](quickstart.md). No unresolved design questions; implementation tasks remain open.

## Complexity Tracking

No constitution violations. Only three pure algorithm modules, one truth adapter and one focused
GUI panel are proposed. Existing state, worker, playback and publisher remain authoritative.
