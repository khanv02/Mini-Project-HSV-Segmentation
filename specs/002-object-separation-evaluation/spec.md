# Feature Specification: HSV Object Analysis, Separation and Evaluation

**Feature Branch**: Existing branch retained; feature directory is independent of branch name.

**Created**: 2026-10-28

**Status**: Implemented and verified on 2026-10-28; see `docs/verification.md` and
`experiments/feature-002/report.md`.

**Input**: Extend the existing desktop application with connected components and contours,
object statistics and minimum-area filtering, optional Distance Transform/Watershed separation,
and ground-truth IoU/Dice evaluation. Preserve HSV as the core and reuse existing workflows.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect Connected Regions (Priority: P1)

As a student, I want to inspect regions selected by HSV and measure them without assuming
each connected region represents a distinct real-world object.

**Why this priority**: Useful independently of Watershed and ground truth.

**Independent Test**: Analyze two separated rectangles and one noise pixel; verify exact
counts, pixel areas, centroids, bounds and aligned contours.

**Acceptance Scenarios**:

1. **Given** a current baseline mask, **When** analysis is enabled, **Then** foreground regions
   have IDs, pixel areas, centroids and bounding boxes; background is excluded.
2. **Given** areas 1, 4 and 9, **When** minimum area is 4 pixels, **Then** retained count is 2,
   raw count is 3, and only the 4- and 9-pixel regions appear in statistics and overlays.
3. **Given** diagonal pixels, **When** connectivity changes between 4 and 8 neighbors,
   **Then** grouping changes accordingly and active connectivity is visible.
4. **Given** empty or entirely filtered masks, **When** analysis completes, **Then** retained
   count is zero, the table is empty, and the application shows a normal empty state.
5. **Given** contours and boxes, **When** zoom changes, **Then** annotations remain aligned
   with source coordinates and source/exported baseline pixels remain unchanged.

---

### User Story 2 - Separate Touching Regions (Priority: P2)

As a student, I want optional Watershed separation of HSV-selected regions so I can inspect
touching-object hypotheses and understand unsuccessful separation.

**Why this priority**: Adds separation while preserving baseline color selection.

**Independent Test**: Use a documented touching-disks fixture yielding two foreground seeds;
verify two labels, compare baseline, then disable separation and verify baseline equality.

**Acceptance Scenarios**:

1. **Given** a baseline result, **When** Watershed is enabled with valid settings, **Then**
   separated regions and boundaries appear with baseline comparison available.
2. **Given** the touching-disks reference fixture, **When** documented settings are applied,
   **Then** two region labels appear inside the HSV-derived foreground domain.
3. **Given** empty foreground or insufficient markers, **When** separation is attempted,
   **Then** an explicit empty/not-applied status explains why; baseline remains available.
4. **Given** separated results, **When** Watershed is disabled, **Then** existing baseline
   mask/result and save behavior remain unchanged.
5. **Given** an unsuitable image, **When** separation is poor, **Then** users can compare
   and adjust settings without any guarantee that physical objects will be separated.

---

### User Story 3 - Evaluate a Binary Prediction (Priority: P2)

As a student, I want IoU and Dice against ground truth so I can quantify overlap separately
from the percentage of pixels selected.

**Why this priority**: Independent quality evidence without requiring Watershed.

**Independent Test**: For prediction/truth sizes 3 and intersection 2, verify IoU=0.5 and
Dice=2/3; also verify disjoint, identical and empty masks.

**Acceptance Scenarios**:

1. **Given** a source, **When** valid same-sized truth is loaded, **Then** truth identity,
   conversion rule and named evaluation target are visible with IoU/Dice.
2. **Given** two empty masks, **When** evaluated, **Then** both scores are 1 with an explicit
   both-empty status; exactly one empty mask yields both scores 0.
3. **Given** wrong dimensions, unsupported format or corrupt truth, **When** loading fails,
   **Then** actionable feedback appears and prior valid source/truth remain unchanged.
4. **Given** truth bound to a paused video frame, **When** playback advances or the source
   changes, **Then** truth and metrics clear until truth is bound to the current frame.
5. **Given** valid evaluation, **When** its confusion overlay is enabled, **Then** a legend
   distinguishes true positives, false positives and false negatives without changing masks.

---

### User Story 4 - Record Extended Experiments (Priority: P3)

As a student, I want reproducible settings and evidence for analysis, separation and evaluation.

**Why this priority**: Connects independently useful algorithms to academic evidence.

**Independent Test**: Publish baseline and extended runs, reconstruct the extended prediction
and metrics, and replay a legacy record without modifying it.

**Acceptance Scenarios**:

1. **Given** a complete current result, **When** recording, **Then** source/frame, baseline,
   optional settings/statuses/statistics and prediction target are captured consistently.
2. **Given** evaluated results, **When** replayed from saved prediction and normalized truth,
   **Then** counts match exactly and scores agree within 1e-12.
3. **Given** legacy records and disabled extensions, **When** replay/recording occurs,
   **Then** existing artifacts remain usable without migration or rewriting.
4. **Given** an artifact write failure, **When** publication fails, **Then** no complete
   record is published and displayed results remain available for retry.

### Edge Cases

- Empty, full, single-pixel, border-touching, thin and holed masks are valid analysis inputs.
  Holes are not objects; contour polygon area is not foreground pixel area.
- Equal-area regions receive deterministic within-frame IDs; IDs never imply tracking.
- Tiny frames, no usable background or fewer than two foreground seeds produce explained
  not-applied separation, never a fabricated split.
- Invalid, nonfinite, fractional or boolean numeric settings are rejected before application.
- Truth is never silently resized, rotated, cropped or interpolated.
- Missing truth means unavailable metrics, not zero quality. Cancellation changes no state.
- Late processing, truth loading or evaluation must not update a newer frame/revision.
- Resource failures preserve the previous valid snapshot and provide recovery guidance.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: HSV and existing optional morphology MUST remain baseline selection. Extensions
  MUST be opt-in and retain default pixels, controls, formats, presets, sampling and exports.
- **FR-002**: Region analysis MUST support 4/8-neighbor connectivity; exclude background;
  expose raw/retained counts, IDs, pixel areas, centroids and source-coordinate bounding boxes.
- **FR-003**: Minimum area MUST be a nonnegative integer in source pixels. Retain area >=
  minimum; filter derived analysis/prediction only, preserving the baseline mask.
- **FR-004**: Users MUST independently toggle contours and boxes and inspect retained region
  statistics. Labels MUST explain that connected regions need not be physical objects.
- **FR-005**: Watershed MUST derive markers from the HSV-derived mask and distance information,
  use the original image, constrain results to the baseline foreground, and expose its marker
  and optional preprocessing settings.
- **FR-006**: Users MUST toggle Watershed and compare baseline to labeled regions/boundaries.
  Applied, empty and not-applied statuses MUST be explicit, with a reason when not applied.
- **FR-007**: Truth loading MUST accept lossless PNG/BMP binary/grayscale masks, palette masks
  resolving to grayscale and equal-channel RGB; reject unequal RGB channels. Ignore alpha with
  disclosure. Values strictly greater than a visible integer threshold (default 0, range
  0..254) become foreground. Require exact dimensions; reject JPEG and unsupported bit depths.
- **FR-008**: Users MUST explicitly select baseline, filtered components or Watershed foreground
  for evaluation. Default is baseline; unavailable targets MUST NOT silently fall back.
- **FR-009**: IoU MUST be intersection/union; Dice MUST be twice intersection divided by the
  sum of foreground sizes. Both-empty scores are 1 with status; one-empty scores are 0.
  Selected-pixel percentage MUST be labeled coverage, never segmentation accuracy.
- **FR-010**: The GUI MUST show truth identity, target, scores in [0,1], empty-case status and
  pending state. A switchable TP/FP/FN overlay MUST have a legend and preserve mask data.
- **FR-011**: Analysis/separation MUST work for images and accepted video frames. Truth MUST
  bind to one session/source/frame, survive parameter edits on that frame and clear on source
  replacement, restart or frame advancement. Loading truth MUST pause video first.
- **FR-012**: Results MUST synchronize source, frame and all settings. Pending/invalid settings
  MUST block recording mislabeled extended results; stale completions MUST be rejected.
- **FR-013**: Extended records MUST capture settings, counts, statuses, prediction target and
  prediction evidence. Evaluated records MUST include normalized truth, original truth identity,
  conversion rule, file/pixel hashes and metrics. Legacy records MUST remain usable unchanged.
- **FR-014**: Failures MUST identify operation, affected input/setting, cause category,
  preserved state and corrective action. Expected inability to separate is a normal status.

### Non-Functional Requirements

- **NFR-001**: Full workflows MUST work offline without new services or accounts.
- **NFR-002**: New algorithms MUST be independently testable; all features MUST have automated
  normal, boundary, failure and affected-workflow acceptance coverage.
- **NFR-003**: Heavy work MUST leave the window interactive. On the documented computer,
  baseline Full-HD edits MUST retain >=95/100 updates within one second. For analysis/Watershed,
  record median/p95 latency and peak memory over 100 edits; >=95/100 scheduled UI heartbeats
  MUST execute within 250 ms while work is pending. No real-time separation guarantee applies.
- **NFR-004**: At 960x640 with histogram visible/hidden, retain three previews of at least
  160x120 drawable pixels and reachable HSV controls. Use collapsible/tabbed extra controls,
  visible keyboard focus, units, validation and explicit unavailable states.
- **NFR-005**: Same source/settings/environment MUST reproduce normalized labels and integer
  counts exactly; metric comparisons use absolute tolerance 1e-12.
- **NFR-006**: Existing image/video lifecycle, sampling, histogram and export regressions MUST
  pass with all new options disabled.

### Expected Inputs and Outputs

| Operation | Input | Output |
| --- | --- | --- |
| Analysis | Baseline mask, connectivity, minimum area | Labels, raw/retained counts, contours, statistics, filtered mask |
| Separation | Original source, baseline mask, settings | Status, labels, boundaries, separated binary foreground |
| Evaluation | Named prediction, normalized matching truth | Overlap counts, IoU/Dice, empty status, confusion display |
| Recording | Complete source/frame/settings snapshot | Record and verifiable local artifacts |

### Key Entities *(include if feature involves data)*

- **Analysis Settings/Result**: Connectivity, minimum area, labels and measured regions.
- **Separation Settings/Result**: Marker settings, status, labels and boundaries.
- **Ground Truth**: Immutable mask, provenance, conversion rule and source/frame binding.
- **Evaluation**: Prediction target, truth, overlap counts, scores and status.
- **Extended Experiment**: Baseline plus optional derived evidence from one snapshot.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Analytical fixtures match exact counts, pixel areas, centroids and boxes for
  both connectivities and minimum-area boundary cases.
- **SC-002**: Touching-disks reference produces two labels; inadequate-marker cases retain
  baseline with truthful status and no crash.
- **SC-003**: All evaluation reference counts match exactly and scores within 1e-12; invalid
  truth cases preserve valid state.
- **SC-004**: Image/video replacement, rapid settings, truth binding and late-completion
  acceptance tests show zero stale statistics or metrics presented as current.
- **SC-005**: Each story has one reproducible extended demonstration; legacy replay passes
  unchanged and failed publication produces no complete record.
- **SC-006**: Existing regressions, NFR-003 responsiveness and NFR-004 layout checks pass with
  actual environment and measurements recorded.

### Demonstration Scenarios

1. **D1**: Two rectangles plus noise; filter noise, inspect measurements and toggle annotations.
2. **D2**: Touching disks; compare separation, tune markers, show a failure and restore baseline.
3. **D3**: Partial overlap with IoU=0.5 and Dice=2/3; inspect confusion regions, then demonstrate
   empty masks and dimension rejection.
4. **D4**: Pause video, bind truth, evaluate, advance and verify clearing; record and replay a
   new frame-bound run.
5. **D5**: Disable extensions; exercise presets, ROI, histogram, export and baseline recording.

## Assumptions

- Extends feature 001. Its exclusion of counting/numerical evaluation is superseded only for
  this enhancement; tracking and learned recognition remain excluded.
- Defaults: analysis disabled, connectivity 8, minimum area 0; Watershed disabled, seed fraction
  0.5 (0 < value < 1), expansion iterations 1 (0..10), odd kernel 3 (3,5,7,9).
- Existing optional morphology is the explicit preprocessing stage; no hidden second cleanup.
- Area is foreground pixel count; coordinates refer to original source pixels. Watershed ridge
  pixels are excluded from its binary prediction and this convention is saved.
- Truth is one binary annotation for an image or paused frame; no annotation editor, automatic
  alignment or truth-video collection is required. TP/FP/FN visualization is included.
- Out of scope: semantic recognition, tracking, guaranteed separation, automatic tuning,
  learned models, cameras/audio, full-video export, databases, GUI migration and physical units.
