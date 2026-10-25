# Tasks: HSV Color Segmentation

**Input**: `specs/001-hsv-color-segmentation/spec.md`, the current `plan.md`, and
`.specify/memory/constitution.md`.

**Planning status**: Design completed on 2026-10-24 in `plan.md`, `research.md`,
`data-model.md`, `contracts/` and `quickstart.md`. T001 is complete at design level.
Phases 1 through 7 (T001-T044) are complete. Experiment evidence uses licensed real photographs,
including one fixed MIT scene captured under two documented directional lights.
Setup, foundation, still-image MVP, video, PNG export and comprehensive recovery checks have passed.

**Execution policy (user instruction)**: Implement and verify one phase at a time,
then stop and report before starting the next phase. See
`docs/implementation-stages.md` for the original eight stage boundaries; the histogram
extension is defined below as Phase 9. The current delivered increment includes the completed
Phase 8 documentation/performance baseline (T045–T048) and Phase 9 (T051-T056).
T049 and dependent T050 are a separate final acceptance/review gate and remain open for genuine
external acceptance. The requested HSV histogram is implemented as Phase 9 (T051-T056), before that
final gate. Histogram implementation and verification evidence are recorded in the Phase 9
tasks and `docs/verification.md`.

**Tests**: Required by FR-017, the constitution, and the user's requested unit-test phase.

**Organization**: Setup and shared foundation first, then story increments. US1 contains the
core algorithm, processing tests, GUI display, and interactive controls. Video and export are
both P2; video precedes export to follow the requested progression. Basic validation belongs
in each increment; US5 adds comprehensive recovery checks. Experiments and documentation follow.
US6 adds source/frame HSV distribution charts using existing dependencies. Stable task IDs are
retained; the new dependency edges place T051-T056 before final acceptance T049-T050.

## Format: `[ID] [P?] [Story] Description`

Every task has a sequential ID, an exact output path, explicit dependencies, and a **Done**
criterion. `[P]` marks tasks that can share a work window after their listed prerequisites
finish; it never overrides dependencies. Story labels match `spec.md`.

## Path Conventions

Design decisions established in T001 (see plan.md and contracts/):

- One local Python 3.11 desktop package at `src/hsv_segmentation/`, with a module entry point.
- Tkinter for the desktop controls, Pillow for image decoding/display and PNG export,
  NumPy for vectorized float64 HSV conversion and arrays, OpenCV for video decoding only, pytest for tests.
  Exact compatible dependency versions are selected and recorded in T002, not assumed here.
- `processing/` contains pure in-memory algorithms; `io/` contains file operations;
  `gui/` contains widgets and interaction; `application/` coordinates sessions and workers.
- Normalized processing input is an RGB uint8 array of shape `(height, width, 3)`.
  HSV uses unrounded floating component values in degrees and percentages, with a documented
  neutral-color hue convention and conversion tolerance. Masks use uint8 values 0 and 255.
- Experiments use local JSON records and PNG artifacts, with no database or service.
- Unit tests live in `tests/unit/`; integration checks in `tests/integration/`;
  reproducible evidence in `experiments/`; explanations in `docs/`.

These decisions match the completed plan. Update dependent artifacts together if the design changes.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Resolve the missing design decisions, then prepare a reproducible student setup.

- [x] T001 Complete `specs/001-hsv-color-segmentation/plan.md` using `$speckit-plan` and reconcile the specification and task defaults; **Depends**: none; **Done**: plan, research, data model, contracts and quickstart are written, all nine constitution gates pass at design level, reuse decisions and numerical conventions are recorded, and earlier analysis findings are synchronized without claiming runtime acceptance.
- [X] T002 Write packaging metadata in `pyproject.toml`, select compatible third-party/runtime/test/build dependencies and pin exact versions in `requirements-lock.txt`; **Depends**: T001; **Done**: dependencies install for Windows CPython 3.11 x64, Tkinter and required libraries import, and exact tool versions are recorded; local package installation waits for the T003 source skeleton.
- [X] T003 [P] Create package skeletons under `src/hsv_segmentation/`, configure package/test discovery in `pyproject.toml`, then install the local package; **Depends**: T002; **Done**: editable installation and independent imports succeed after skeleton creation, pytest finds the intended test roots, and an initially empty collection is distinguished from an import/configuration failure.
- [X] T004 [P] Add environment, generated-output, and cache exclusions to `.gitignore` and setup commands to `README.md`; **Depends**: T002; **Done**: a student can create the environment and install the locked dependencies using copyable Windows commands, while generated files are distinguished from retained experiment evidence.

**Checkpoint**: Plan decisions are concrete; package installation and test discovery work.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared data and session invariants without mixing GUI, algorithms, and I/O.

- [X] T005 Define media identity, threshold and result snapshot records in `src/hsv_segmentation/models.py` according to `specs/001-hsv-color-segmentation/data-model.md`; **Depends**: T003, T004; **Done**: typed records enforce positive dimensions with width*height <=12,000,000, immutable six-bound snapshots, nonnegative revisions, image frame_index=null/video frame_index>=0, valid session identity, and exact source/threshold/frame relationships without GUI dependencies.
- [X] T006 [P] Define input, validation, decode, and write error types in `src/hsv_segmentation/errors.py`; **Depends**: T005; **Done**: lower layers can signal distinct actionable failures without displaying dialogs or importing GUI modules.
- [X] T007 [P] Create analytical RGB/HSV fixtures and expected masks in `tests/fixtures/color_cases.py`; **Depends**: T005; **Done**: primaries, neutral colors, exact and nextafter boundaries, RGB (255,0,1) near 360 degrees, default [0,360] and independent colorsys comparisons have explicit expected outcomes; circular hue and S/V errors use absolute tolerance 1e-10 with relative tolerance zero.

**Checkpoint**: Shared contracts and independent reference data are available. No story
implementation starts until T005 through T007 are complete.

## Phase 3: User Story 1 - Segment an Image Interactively (Priority: P1) MVP

**Goal**: Open an image, adjust all HSV bounds, and compare original, mask, and extracted result.

**Independent Test**: Load the analytical color image, change all six controls, verify inclusive
membership and hue wraparound, and see synchronized aspect-preserving views without video,
export, or experiment features.

### Processing Tests and Core HSV Algorithm

Write the relevant tests first and observe meaningful failures before implementation.

- [X] T008 [P] [US1] Add conversion/input-contract tests in `tests/unit/test_color_conversion.py`; **Depends**: T006, T007; **Done**: hand-derived and independent colorsys cases verify float64 degree/percentage results within absolute tolerance 1e-10 (relative tolerance zero), neutral hue=0, channel order, invalid shape/type, size limits and source immutability, and fail meaningfully before conversion exists.
- [X] T009 [P] [US1] Add threshold/extraction tests in `tests/unit/test_segmentation.py`; **Depends**: T006, T007; **Done**: direct HSV fixtures and adjacent nextafter values verify inclusive/equal bounds, hue wraparound, all/none selection, default [0,360] including H>359, rejection of bool/fractional/nonfinite bounds, exact 0/255 masks, shape/type mismatches, retained RGB and no mutation.
- [X] T010 [US1] Implement vectorized NumPy float64 RGB-to-HSV conversion in `src/hsv_segmentation/processing/color.py`; **Depends**: T008; **Done**: all conversion tests pass against `specs/001-hsv-color-segmentation/contracts/processing.md`, guarded max/min/delta equations preserve fractional values with neutral H=0, and processing imports neither GUI nor file I/O; OpenCV is reserved for video.
- [X] T011 [US1] Implement threshold validation in `src/hsv_segmentation/processing/thresholds.py`; **Depends**: T009, T010; **Done**: integer lower H 0..359, upper H 0..360, S/V 0..100 and ordered S/V are enforced; upper 360 stays an endpoint, reversed hue stays valid, bool/fractional/nonfinite/missing values are rejected, and no bound is silently rounded/clamped.
- [X] T012 [US1] Implement mask generation and extraction in `src/hsv_segmentation/processing/segmentation.py`; **Depends**: T010, T011; **Done**: every T009 test passes, selection intersects all three inclusive intervals, and results retain original resolution and selected RGB pixel values.
- [X] T013 [US1] Execute the processing unit suite and record commands and results in `docs/verification.md`; **Depends**: T012; **Done**: every core function has independent normal, boundary, and applicable invalid-input tests, all pass without starting a GUI, and any discrepancy is fixed before GUI integration.

### GUI Layout and Image Display

- [X] T014 [P] [US1] Add image-load normalization tests in `tests/integration/test_image_input.py`; **Depends**: T013; **Done**: temporary PNG, JPEG, BMP, grayscale, and transparent inputs define expected RGB normalization and cancellation/failure preservation, with failing tests for missing behavior.
- [X] T015 [P] [US1] Build the named window and three labeled aspect-preserving views in `src/hsv_segmentation/gui/main_window.py` and `src/hsv_segmentation/gui/image_view.py`; **Depends**: T013; **Done**: the window separates input, parameter, and visualization sections and displays supplied original/mask/result arrays without resizing processing data.
- [X] T016 [US1] Implement image file reading in `src/hsv_segmentation/io/images.py`; **Depends**: T014; **Done**: PNG/JPEG/BMP decode to the processing RGB contract, grayscale replicates channels, alpha is ignored as specified, and temporary-file normalization tests pass.
- [X] T017 [US1] Implement image session coordination in `src/hsv_segmentation/application/session.py`; **Depends**: T015, T016; **Done**: first open uses (0,360,0,100,0,100), subsequent opens retain valid bounds, complete decoding/resource validation precedes commit, and failed/cancelled candidates preserve the prior session.

### Interactive HSV Threshold Controls

- [X] T018 [US1] Add six synchronized numeric controls with range labels in `src/hsv_segmentation/gui/threshold_controls.py`; **Depends**: T017; **Done**: all six values are editable, allowed units/ranges and hue wraparound are explained, invalid input has specific feedback, and invalid edits never become active settings.
- [X] T019 [US1] Add revision-aware processing coordination in `src/hsv_segmentation/application/processing_worker.py`; **Depends**: T018; **Done**: valid edits trigger automatic recomputation, GUI updates occur on the GUI thread, rapid edits coalesce, obsolete results are discarded, and source/result/threshold revisions stay synchronized.
- [X] T020 [US1] Connect input actions, controls, session, worker, and display through `src/hsv_segmentation/gui/controller.py` and `src/hsv_segmentation/__main__.py`; **Depends**: T019; **Done**: `python -m hsv_segmentation` runs the image workflow, all three views agree, and closing the window releases work without freezing.
- [X] T021 [US1] Add session and stale-result regression checks in `tests/integration/test_image_session.py` and record the image demonstration in `docs/verification.md`; **Depends**: T020; **Done**: all US1 scenarios pass, final rapid-edit output matches final thresholds, file contents remain unchanged, and the application stays usable while processing.

**Checkpoint**: Working MVP. Image segmentation, independent core tests, labeled comparison,
and six interactive controls work before adding video or export.

## Phase 4: User Story 3 - Segment Video Frames (Priority: P2)

**Goal**: View successive video frames and adjust segmentation while playing or paused.

**Independent Test**: Open a short color video, inspect its first frame, play, pause, adjust
thresholds while paused, reach the end, and restart; all three views share a frame position.
Frame export is verified in Phase 5 after US2 exists.

### Tests for User Story 3

- [X] T022 [P] [US3] Add video reader lifecycle checks in `tests/integration/test_video_input.py`; **Depends**: T021; **Done**: short reproducibly generated MP4/AVI fixtures and reader doubles distinguish first-frame load, normal end, empty input, decode failure, restart, replacement, and cleanup; missing behavior initially fails.
- [X] T023 [P] [US3] Add playback/session tests in `tests/integration/test_playback.py`; **Depends**: T021; **Done**: deterministic frame doubles specify play/pause, revision matching, paused reprocessing, end/restart, and replacing a source without displaying obsolete frames.

### Implementation for User Story 3

- [X] T024 [US3] Implement bounded video decoding/resource cleanup in `src/hsv_segmentation/io/video.py`; **Depends**: T022; **Done**: locally decodable MP4/AVI yield RGB and frame positions, first-frame validation precedes commit, image/frame pixel limits apply, captures are released, explicit decode failures and known-fixture EOF are distinguished, and ambiguous termination uses the honest message in `specs/001-hsv-color-segmentation/contracts/desktop-workflow.md` rather than assuming false read means EOF.
- [X] T025 [US3] Implement playback orchestration in `src/hsv_segmentation/application/playback.py`; **Depends**: T023, T024; **Done**: the first frame opens paused, playback/pause/end/restart follow the tests, paused edits reprocess the retained frame, and old input resources/work are released on replacement.
- [X] T026 [US3] Add video controls and frame position to `src/hsv_segmentation/gui/main_window.py` and wire them in `src/hsv_segmentation/gui/controller.py`; **Depends**: T025; **Done**: all views remain synchronized throughout the playback acceptance flow, decode failures retain the last valid frame, and playback can be slower than real time without blocking GUI interaction.
- [X] T027 [US3] Record video format/encoding and playback acceptance evidence in `docs/verification.md`; **Depends**: T026; **Done**: a real supported video completes opening, playing, pausing, paused edits, end, restart and source replacement, with clean shutdown and all automated video checks passing.

**Checkpoint**: Video segmentation works; no audio, tracking, seeking, or full-video export added.

## Phase 5: User Story 2 - Save Results for a Report (Priority: P2)

**Goal**: Export accurate full-resolution PNG masks and extracted images, including video frames.

**Independent Test**: Export known image and paused-video outputs, reopen them, and compare
dimensions and pixels; exercise overwrite, cancellation, and unwritable destinations.

### Tests for User Story 2

- [X] T028 [P] [US2] Add lossless image-output tests in `tests/integration/test_image_export.py`; **Depends**: T027; **Done**: tests specify exact PNG round trips, 0/255 mask values, unchanged source dimensions, and write failure behavior using temporary directories.
- [X] T029 [P] [US2] Add export availability and snapshot tests in `tests/integration/test_export_session.py`; **Depends**: T027; **Done**: tests reject absent/pending results, verify a consistent playing-video frame/threshold snapshot, and specify cancellation and overwrite-decline preservation.
  Include a controlled delayed writer: encoding runs outside the GUI thread, interaction is serviced before write completion, duplicate save/record actions are disabled, source replacement preserves captured identity, completion/failure is delivered on the GUI thread, and closing during a write causes no stale UI callback (FR-012).

### Implementation for User Story 2

- [X] T030 [US2] Implement PNG mask/result writing in `src/hsv_segmentation/io/export.py`; **Depends**: T028; **Done**: output tests pass at source resolution with exact decoded pixels, and write failures propagate an actionable error without changing the live result.
- [X] T031 [US2] Add save actions and consistent snapshot capture in `src/hsv_segmentation/gui/controller.py`; **Depends**: T029, T030; **Done**: unavailable/pending outputs cannot be saved, overwrite requires confirmation, cancellation preserves files/state, and success identifies the saved path for one complete source/frame/threshold snapshot.
  Dispatch PNG writing through the serialized background worker after capturing an immutable snapshot; allow one save/record operation at a time, disable duplicate write actions, and deliver status through main-thread polling with closed-window guards (FR-011, FR-012).
- [X] T032 [US2] Verify image and video-frame exports and record evidence in `docs/verification.md`; **Depends**: T031; **Done**: all US2 scenarios and US3 frame-export scenario pass, including exact pixel comparisons, error recovery, and continued playback consistency.
  Record delayed-write interaction and close-during-write results from T029; successful background completion must identify the captured output even if the active source has changed (FR-012).

**Checkpoint**: Images and individual video frames can be exported reliably.

## Phase 6: User Story 5 - Recover from Invalid Input (Priority: P2)

**Goal**: Keep demonstrations usable through invalid files, parameter mistakes, and failed saves.

**Independent Test**: Starting with a valid session, try each invalid operation and cancellation,
then continue with another valid open/edit/save without restarting.

### Tests for User Story 5

- [X] T033 [P] [US5] Add a recovery matrix in `tests/integration/test_error_recovery.py`; **Depends**: T032; **Done**: missing, unreadable, corrupt, unsupported and resource-exhausting inputs, decode interruption, bad parameters, cancelled dialogs and failed saves each have a specified expected state and corrective message.
  For each failure assert operation, affected file/parameter, cause category, preserved session state and a concrete corrective action; parameter errors include the allowed range/ordering rule, uncertain video termination is not asserted as a known cause, and cancellation requires no error message (FR-013, SC-007).
- [X] T034 [P] [US5] Add GUI recovery acceptance steps in `docs/acceptance.md`; **Depends**: T032; **Done**: each recovery-matrix case specifies actions, expected message, preserved source/threshold/output state, and a subsequent valid action, including the three labeled layout sections.
  Include FR-013 content checks and prepare the FMT-001-FMT-007 inventory from spec.md with paths/generation commands, hashes, expected normalization, and actual codec/backend/environment details for both videos; missing required fixtures or decoder support stay explicit (FR-002, SC-001, SC-007).

### Implementation for User Story 5

- [X] T035 [US5] Complete actionable failure handling in `src/hsv_segmentation/gui/controller.py`, `src/hsv_segmentation/application/session.py`, and `src/hsv_segmentation/application/playback.py`; **Depends**: T033, T034; **Done**: recovery tests pass, no failed open discards the previous valid session, invalid edits do not relabel old results, and failures do not crash the application.
- [X] T036 [US5] Execute the GUI recovery matrix and retain observations in `docs/verification.md`; **Depends**: T035; **Done**: every error and cancellation case passes with a successful subsequent operation, including cleanly stopping failed playback and handling oversized inputs without an unresponsive window.

**Checkpoint**: Comprehensive error recovery validated; essential error handling already existed
in the relevant earlier increments rather than being deferred until this phase.

## Phase 7: User Story 4 - Record and Compare Experiments (Priority: P3)

**Goal**: Persist reproducible runs and demonstrate segmentation quality across at least 10 images.

**Independent Test**: Record two threshold settings for each of 10 images, inspect saved artifacts,
and reproduce three selected runs from source identities and recorded thresholds.

### Tests for User Story 4

- [X] T037 [P] [US4] Define record persistence/failure tests in `tests/integration/test_experiment_records.py`; **Depends**: T036; **Done**: tests enforce schema_version=1, unique UUID run_id, UTC ISO timestamp, valid six integer bounds/units, dimensions/frame identity, nonempty lighting/observations, environment reference, valid relative output paths and 64-character lowercase SHA-256 hashes per `specs/001-hsv-color-segmentation/contracts/experiment-record.md`; failed artifacts cannot publish a complete record.
  Use delayed hash/PNG/JSON operations to check background execution, responsive interaction, one active write with duplicate actions disabled, immutable captured identity, main-thread notifications, and safe close during publication (FR-012, FR-014).
- [X] T038 [P] [US4] Prepare `experiments/inputs/` and `experiments/manifest.json`; **Depends**: T036; **Done**: at least 10 distinct accessible images have source/permission metadata, hashes and lighting descriptions, including one photographed scene under two real lighting conditions; synthetic cases are identified separately from photographed evidence.

### Implementation for User Story 4

- [X] T039 [US4] Implement local JSON experiment export in `src/hsv_segmentation/io/experiments.py`; **Depends**: T037; **Done**: each run has a distinct identity and complete metadata, paths resolve to successful PNG exports, and record publication occurs only after all referenced outputs succeed.
- [X] T040 [US4] Add lighting/observation fields and a Record Experiment action in `src/hsv_segmentation/gui/experiment_panel.py` and `src/hsv_segmentation/gui/controller.py`; **Depends**: T039; **Done**: users can capture one consistent result snapshot with their descriptions, see saved locations, and retry failed export without losing results.
  Capture descriptions and snapshot on the GUI thread, then dispatch hashing, PNG writes and JSON publication through the same serialized background-write path as T031; apply the one-active-write policy and safe completion/failure handoff verified by T037 (FR-012, FR-014).
- [X] T041 [US4] Create a repeatable experiment procedure and environment record in `experiments/README.md` and `experiments/environment.json`; **Depends**: T038, T040; **Done**: a student can locate every input, apply two documented threshold sets per image, reproduce the environment, and interpret the saved mask/result/record relationships.
- [X] T042 [US4] Execute and retain at least 20 complete runs in `experiments/runs/`; **Depends**: T041; **Done**: all 10 images have two distinct threshold settings and saved outputs, records include lighting and qualitative observations, and failures are resolved rather than recorded as successful evidence.
- [X] T043 [US4] Add automatic replay checks in `tests/integration/test_experiment_reproduction.py` and prepare `experiments/reproduction.md`; **Depends**: T042; **Done**: three recorded runs reproduce identical decoded pixels automatically after source/environment checks, and the independent student/date/outcome form is prepared with human acceptance explicitly pending rather than blocking documentation preparation.
- [X] T044 [US4] Prepare labeled visual comparisons in `experiments/report.md`; **Depends**: T042; **Done**: every image has original/mask/result comparisons for both threshold sets and observations about missed targets, unwanted selection and lighting effects, without claiming unmeasured accuracy scores.

**Checkpoint**: Experiment recording works and the required collection, comparisons, and
reproducibility evidence are complete. Missing real inputs or independent participants remain
visible unmet criteria; do not invent evidence.

## Phase 8: Documentation, Performance and Demo Baseline

**Purpose**: Verify responsiveness, explain the algorithm, and prepare the academic demonstration.

- [X] T045 [P] Document RGB/HSV conversion, formulas/conventions, precision, inclusive masks and hue wraparound in `docs/algorithm.md`; **Depends**: T036; **Done**: explanations match the tested implementation, define units and neutral behavior, explain grayscale/alpha handling, and describe limitations in presentation-ready terms.
- [X] T046 [P] Measure 100 threshold changes on a 1920x1080 still image and retain the procedure/results in `experiments/performance.md`; **Depends**: T036; **Done**: the documented computer meets at least 95 updates within one second, final outputs match final controls, and any needed fixes are made and remeasured before marking this task complete.
- [X] T047 Update `README.md` and `specs/001-hsv-color-segmentation/quickstart.md`; **Depends**: T043, T044, T045, T046; **Done**: setup, launch, tests, supported formats/codecs, six controls, video behavior, export, experiment replay, limitations and offline independence have accurate copyable instructions.
- [X] T048 Prepare `docs/demo.md`; **Depends**: T047; **Done**: a timed walkthrough covers the image MVP, video, export, recovery, all 10 experiment images and lighting comparisons, with matching saved artifacts and an explanation of why HSV is used.

**Checkpoint**: The baseline documentation, performance evidence and demo script are complete.
The pending human acceptance and final review belong to the separate gate after Phase 9.

## Phase 9: User Story 6 - Inspect HSV Distributions (Priority: P2)

**Goal**: Help students choose the six manual HSV bounds using distributions of the current
source/frame, without altering conversion, threshold membership, exports or recorded results.

**Independent Test**: Open a known-color image, inspect exact H/S/V counts and the reported
low-saturation exclusion, move ordered/wrapped bounds, then replace the input and advance/pause
a video. Verify source/frame identity, overlays, unchanged source counts on threshold-only edits,
and segmentation pixels against the existing pure implementation.

**Ordering**: T048 supplies the delivered baseline. Complete this extension before T049-T050
so the final acceptance assesses the delivered version including histograms. This phase does
not depend on collecting the still-pending human acceptance evidence first.

- [X] T051 [P] [US6] Define the histogram data/processing contracts in `specs/001-hsv-color-segmentation/data-model.md` and `specs/001-hsv-color-segmentation/contracts/processing.md`, and add analytical tests in `tests/unit/test_histogram.py`; **Depends**: T048; **Done**: cases specify 360 H bins, 101 S/V bins, integer-part bin assignment with exact 100 in the last S/V bin, exact S=5 inclusion and S<5 exclusion from hue only, excluded-count reporting, count totals, empty-hue/grayscale cases, invalid inputs and preservation of source HSV values.
- [X] T052 [US6] Implement pure histogram counting in `src/hsv_segmentation/processing/histogram.py` and its immutable result representation in `src/hsv_segmentation/models.py`; **Depends**: T051; **Done**: analytical counts pass exactly, H total plus excluded count and each S/V total equal source pixel count, arrays are independent of thresholds, inputs are not mutated, and the implementation imports neither GUI nor file I/O.
- [X] T053 [P] [US6] Specify histogram interactions in `specs/001-hsv-color-segmentation/contracts/desktop-workflow.md` and add GUI integration checks in `tests/integration/test_histogram_panel.py`; **Depends**: T048; **Done**: checks cover show/hide, all three result views remaining available, axis/count labels and the fixed S>=5 hue note, ordered/equal/full/wrapped bounds, no-media and empty-hue states, invalid/pending edits, source/frame replacement, failed-open preservation and stale-completion rejection. Verify overlays use numeric coordinates without snapping to bins, equal bounds draw a labeled line, and S=5.9 in bin 5 remains excluded by S=5..5. At a 960x640 client area with 100% display scaling, showing and hiding the panel preserves unclipped charts/labels/markers/toggle/controls without overlap or scrolling and at least a 160x120 preview area per result view.
- [X] T054 [US6] Add the compact show/hide histogram widget in `src/hsv_segmentation/gui/hsv_histogram.py` and layout support in `src/hsv_segmentation/gui/main_window.py`; **Depends**: T052, T053; **Done**: Tkinter Canvas renders three source frequency charts, active valid ranges and the excluded hue count. Overlay boundaries map to the numeric H 0..360 and S/V 0..100 axes independently of bar widths, equal bounds appear as a labeled line, and wrapped hue marks both axis ends; shaded bins are not presented as exact selected-pixel counts. At a 960x640 client area and 100% display scaling, charts/labels/markers/toggle/six controls remain visible without overlap or scrolling and each result view has at least a 160x120 aspect-preserving preview area. Viewing or hiding charts does not edit thresholds or outputs; no plotting dependency is added.
- [X] T055 [US6] Coordinate histogram counts and overlays in `src/hsv_segmentation/application/processing_worker.py` and `src/hsv_segmentation/gui/controller.py`; **Depends**: T054; **Done**: counts are computed outside GUI handlers and cached by accepted session/frame identity, threshold-only edits reuse counts and update overlays, source/frame changes invalidate the cache, invalid controls retain a clearly marked last-valid overlay, and delayed/replaced work cannot publish stale charts. Image/video masks, exports and experiment artifacts retain existing exact-pixel behavior.
- [X] T056 [US6] Validate the histogram workflow and document it in `docs/algorithm.md`, `docs/demo.md`, `README.md`, `specs/001-hsv-color-segmentation/quickstart.md`, `docs/implementation-stages.md` and `docs/verification.md`; **Depends**: T055; **Done**: relevant analytical/integration checks and unchanged segmentation/replay checks pass, FR-018/SC-009 have recorded evidence, the 100-edit Full-HD benchmark meets SC-003 with the panel visible, and `experiments/performance.md` records the new measurement separately from the pre-histogram baseline. Explain bins, the fixed hue display cutoff, overlays and manual selection; show the current image and video frame without claiming Otsu or automatic threshold selection.

**Checkpoint**: Histogram counts and source/frame synchronization are verified, the six-bound
segmentation semantics are preserved, and the final acceptance T049-T050 can assess this version.

## Phase 10: User Story 7 - Work in a Clean Analysis Workspace (Priority: P1)

**Goal**: Give the existing academic workflow a clear visual hierarchy, compact channel-based
HSV inspector, contextual video controls and consistent accessible styling without changing
processing or persistence behavior.

**Independent Test**: Exercise empty, image and video contexts at 960x640 and a large desktop
size, with the histogram shown and hidden. Verify semantic styles, channel grouping, contextual
controls, keyboard shortcuts, visible focus and three usable previews.

- [X] T057 [P] [US7] Amend the workspace requirements and design decisions in `specs/001-hsv-color-segmentation/spec.md`, `specs/001-hsv-color-segmentation/plan.md`, `specs/001-hsv-color-segmentation/research.md`, `specs/001-hsv-color-segmentation/data-model.md`, `specs/001-hsv-color-segmentation/contracts/desktop-workflow.md` and `specs/001-hsv-color-segmentation/quickstart.md`; **Depends**: T056; **Done**: US7, FR-019 through FR-024 and SC-010 through SC-012 define the clean workspace without changing segmentation semantics.
- [X] T058 [US7] Add GUI acceptance tests for semantic style tokens, vertical channel grouping, contextual playback visibility, keyboard shortcuts and minimum-size previews in `tests/integration/test_workspace_ui.py`; **Depends**: T057; **Done**: checks fail against the pre-refresh workspace and cover empty, image and video presentation states.
- [X] T059 [US7] Implement the semantic light desktop theme and focus/spacing tokens in `src/hsv_segmentation/gui/theme.py`; **Depends**: T058; **Done**: the shared style exposes background, surface, text, muted, border, primary, focus, disabled and error roles using native system typography without a new dependency.
- [X] T060 [US7] Recompose the six controls into Hue, Saturation and Value groups in `src/hsv_segmentation/gui/threshold_controls.py` and align morphology controls in `src/hsv_segmentation/gui/morphology_controls.py`; **Depends**: T059; **Done**: lower/upper controls remain synchronized and validated while the inspector uses a vertical channel hierarchy and compact help text.
- [X] T061 [US7] Recompose the command, inspector, visualization and status regions and add contextual video visibility plus keyboard shortcuts in `src/hsv_segmentation/gui/main_window.py`; **Depends**: T060; **Done**: previews own the flexible area, video controls appear only for video states, hidden controls cannot retain focus, and existing controller-facing widget attributes remain compatible.
- [X] T062 [P] [US7] Apply the semantic canvas, histogram, tooltip and experiment-dialog colors in `src/hsv_segmentation/gui/image_view.py`, `src/hsv_segmentation/gui/hsv_histogram.py`, `src/hsv_segmentation/gui/tooltips.py` and `src/hsv_segmentation/gui/experiment_panel.py`; **Depends**: T059; **Done**: custom Tk surfaces match the shared theme, retain contrast, and do not change image/histogram values.
- [X] T063 [US7] Run focused GUI, processing and export regression tests and fix any layout or behavior regressions in `src/hsv_segmentation/gui/` and `tests/integration/test_workspace_ui.py`; **Depends**: T061, T062; **Done**: all US7 tests and existing GUI integration tests pass at the supported minimum size.
- [X] T064 [US7] Update the workspace walkthrough and verification evidence in `README.md`, `docs/demo.md` and `docs/verification.md`, then run the full automated suite; **Depends**: T063; **Done**: documentation matches the delivered hierarchy and the full suite passes without claiming the pending independent-student acceptance.

**Checkpoint**: The refreshed workspace is visually consistent and context-aware while all prior
image, video, histogram, export and experiment workflows remain intact.

## Final Acceptance and Review Gate

**Purpose**: Accept the complete version after Phase 9, including genuine independent student
checks. These tasks retain their original IDs for traceability and are no longer part of Phase 8.

- [ ] T049 Run the full automated/offline acceptance workflow and independent student checks, recording outcomes in `docs/verification.md` and `experiments/reproduction.md`; **Depends**: T048, T056, T064; **Done**: automated tests pass, every FR/SC has evidence, a second student genuinely reproduces three runs, and a student completes the documented image/edit/compare/save flow within five minutes without help; unavailable external acceptance keeps this final task incomplete.
  Populate the evidence matrix for all 27 FR/SC IDs below with covering task IDs, test/procedure, command/actions, actual outcome and evidence location. Include histogram evidence from T056. Execute every required FMT case on the recorded demonstration computer; skipped codecs, missing fixtures and pending human checks remain unmet acceptance.
- [ ] T050 Review module boundaries, naming, dependency necessity, and constitution compliance in `specs/001-hsv-color-segmentation/plan.md` and `docs/verification.md`; **Depends**: T049; **Done**: processing imports neither GUI nor file I/O, every core function has independent tests, no unused frameworks/services or out-of-scope features exist, and every remaining acceptance limitation is identified.

## Dependencies & Execution Order

### Phase Dependencies

```text
Setup T001-T004
  -> Foundation T005-T007
  -> US1 T008-T021 (working image MVP)
  -> US3 T022-T027 (video)
  -> US2 T028-T032 (image/frame export)
  -> US5 T033-T036 (comprehensive recovery)
  -> US4 T037-T044 (records and 10-image evaluation)
  -> Delivered documentation/performance baseline T045-T048
  -> US6 T051-T056 (implemented HSV histograms)
  -> US7 T057-T064 (clean analysis workspace)
  -> Final acceptance/review T049-T050

After US5: T045 algorithm docs and T046 performance evidence can overlap US4.
```

T003 and T004 must both finish before Phase 2. Within phases, follow each task's explicit
prerequisites. A passing lower-level unit test does not replace the story checkpoint.
Within the original phases, numbering gives the default sequential order subject to the
parallel opportunities below. For the extension, the explicit sequence is T048 -> T051-T056
-> T049 -> T050; stable IDs do not override these dependency edges.

### User Story Dependencies

| Story | Prerequisite | Independently checked result |
| --- | --- | --- |
| US1 | Shared foundation | Interactive still-image segmentation with exact reference masks |
| US3 | US1 | Playback, pause, edit and restart on synchronized frames |
| US2 | US1 and US3 in this schedule | Lossless still/frame exports and overwrite/failure handling |
| US5 | US1, US3 and US2 | Error recovery with a preserved session and subsequent valid action |
| US4 | Working export and recovery | Complete experiment records, 20 runs and replayable comparisons |
| US6 | Delivered Phase 8 automated/documentation baseline T048 | Exact source/frame distributions, valid overlays and unchanged segmentation semantics |
| US7 | US6 delivered | Clean context-aware workspace with unchanged processing and three usable previews |

Export could be implemented immediately after US1 if delivery priorities change; move its
video-specific checks after US3. This list keeps video before export as the user suggested.
Stories are incremental extensions, not falsely independent implementations of the same core.

### Within Each User Story

1. Specify expected outcomes in tests before adding the behavior; verify meaningful failures.
2. Implement data/processing or I/O before wiring the GUI.
3. Run automated checks, then the independent story acceptance scenario.
4. Preserve earlier working increments; do not mark tasks complete based only on code presence.

### Parallel Opportunities

Parallel windows are T003/T004 after T002; T006/T007 after T005;
T008/T009 after foundation; T014/T015 after T013;
T022/T023 after T021; T028/T029 after T027;
T033/T034 after T032; and T037/T038/T045/T046 after T036.
For US6, T051 core contracts/tests and T053 workflow contracts/tests can run after T048 in
separate files; T052 can follow T051 while T053 is prepared. GUI integration follows both.
These windows modify distinct files. Coordinate any later tasks sharing the controller,
verification log or plan sequentially. No sub-agents are required by this task list.

## Parallel Examples by User Story

| Story | Tasks that may run together | Prerequisite |
| --- | --- | --- |
| US1 | T008 conversion tests and T009 segmentation tests | Shared foundation complete |
| US1 | T014 image-input tests and T015 view implementation | T013 processing checks pass |
| US3 | T022 reader tests and T023 playback tests | T021 MVP validated |
| US2 | T028 PNG tests and T029 snapshot tests | T027 video validated |
| US5 | T033 recovery tests and T034 GUI acceptance procedure | T032 export validated |
| US4 | T037 persistence tests and T038 image collection | T036 recovery validated |
| US6 | T051 core contracts/tests and T053 GUI contracts/tests | T048 delivered baseline |
| US7 | T059 theme and T062 custom-surface styling after T058 | T058 workspace tests exist |

## Implementation Strategy

### MVP First (User Story 1 Only)

Complete T001-T021. Demonstrate opening a supported image, changing all six bounds, hue
wraparound, and comparing the original/mask/result. Verify core tests pass independently of
the GUI. This is the first working MVP; video and export are subsequent required increments,
not optional replacements for the image MVP.

### Incremental Delivery

1. Validate the image MVP before video work.
2. Add video, then image/frame export and comprehensive recovery.
3. Add experiment capture and the 10-image/20-run evaluation.
4. Finish measured responsiveness, student reproduction, documentation and the demo.
5. Add the requested HSV histogram aid in T051-T056, then complete T049-T050 on that version.
6. Refresh the workspace in T057-T064, then complete T049-T050 on the delivered UI.
7. Keep counting, tracking, machine learning, automatic threshold selection, audio, full-video
   export, databases and services outside this implementation.

### Requested Stage Coverage

| Requested stage | Tasks |
| --- | --- |
| Project setup and dependencies | T001-T007 |
| Core HSV segmentation | T010-T012 |
| Unit tests for image processing | T007-T009, T013 |
| GUI layout and image display | T014-T017, T020 |
| Interactive HSV controls | T018-T021 |
| Video input support | T022-T027 |
| Save/export | T028-T032, T037, T039-T040 |
| Validation/error handling | T006, T011, T018, T029, T033-T036 |
| Testing with at least 10 images | T038, T041-T044 |
| Documentation/demo | T004, T045-T050 |
| HSV histogram assistance | T051-T056 |
| Clean analysis workspace | T057-T064 |

## Requirement-to-Task Traceability

This table maps planned implementation and verification coverage, not acceptance status.
T056 records histogram and updated performance evidence; T049 completes actual evidence for
every row in `docs/verification.md`. Checked tasks alone
do not substitute for the specified automated, GUI or independent student checks.

| Requirement ID | Covering task IDs | Expected evidence |
| --- | --- | --- |
| FR-001 | T015, T020, T034 | Window title and three labeled sections |
| FR-002 | T014, T016, T022, T024, T027, T034, T047, T049 | Seven-case format inventory and codec/backend results |
| FR-003 | T017, T020, T025, T026 | Initial image/frame and matching outputs |
| FR-004 | T008, T009, T010, T011, T012, T045 | Conversion and segmentation tests with documented equations |
| FR-005 | T011, T018, T045 | Six integer controls, units and range validation |
| FR-006 | T009, T011, T012 | Inclusive/equal bounds and hue-wrap tests |
| FR-007 | T009, T012, T021, T028, T030 | Exact mask/result pixels, dimensions and source preservation |
| FR-008 | T018, T019, T020, T021, T033, T035 | Automatic update, invalid-edit and stale-result checks |
| FR-009 | T015, T020, T021, T026 | Aspect-preserving synchronized views |
| FR-010 | T022, T023, T024, T025, T026, T027 | Playback lifecycle, position and paused edits |
| FR-011 | T028, T029, T030, T031, T032 | Lossless still/frame PNG round trips and snapshot identity |
| FR-012 | T029, T030, T031, T032, T037, T040 | Export availability, overwrite/cancel, delayed writes and safe UI handoff |
| FR-013 | T006, T024, T030, T033, T034, T035, T036 | Required message contents, preserved state and recovery |
| FR-014 | T005, T037, T039, T040 | Complete records and publication-failure checks |
| FR-015 | T038, T041, T042, T043, T044, T049 | Input provenance, environment, twenty runs and reproduction |
| FR-016 | T002, T003, T004, T047, T049, T050 | Installation and full offline acceptance |
| FR-017 | T007, T008, T009, T010, T011, T012, T013, T045, T050 | Independent core tests and algorithm explanations |
| FR-018 | T051, T052, T053, T054, T055, T056 | Exact bin counts, low-saturation hue exclusion, active overlays and current source/frame identity |
| FR-019 | T057, T058, T059, T062, T063 | Semantic visual roles, contrast and consistent native styling |
| FR-020 | T057, T058, T060, T063 | Vertical H/S/V groups with unchanged six-bound behavior |
| FR-021 | T057, T058, T061, T063 | Contextual command and playback-state inventory |
| FR-022 | T058, T061, T063 | Minimum-size three-preview layout checks |
| FR-023 | T058, T061, T063, T064 | Keyboard shortcuts, traversal and focus walkthrough |
| FR-024 | T059, T061, T062, T063 | Stable non-blocking native state changes |
| SC-001 | T014, T016, T022, T024, T027, T034, T049 | All FMT cases and complete playback walkthrough |
| SC-002 | T007, T008, T009, T010, T011, T012, T013 | Exact known-color masks and retained colors |
| SC-003 | T019, T021, T046, T056 | Baseline and histogram-visible 100-change timings with final revision consistency |
| SC-004 | T028, T029, T030, T031, T032 | Source-resolution exact decoded-pixel comparisons |
| SC-005 | T037, T038, T039, T040, T041, T042, T043, T049 | Twenty runs, lighting coverage and three independent replays |
| SC-006 | T047, T048, T049 | Timed student workflow without assistance |
| SC-007 | T033, T034, T035, T036, T049 | Message-content matrix and subsequent valid operations |
| SC-008 | T038, T042, T044, T048, T049 | Labeled ten-image comparisons and observations |
| SC-009 | T051, T052, T053, T054, T055, T056 | Analytical counts, stable source counts during edits, wrapped overlays and preserved views |
| SC-010 | T058, T061, T063 | 960x640 and large-window layout checks with histogram states |
| SC-011 | T058, T061, T063 | Empty/image/video contextual-control inventory |
| SC-012 | T058, T061, T064 | Keyboard-only shortcut and focus walkthrough |

## Notes

- T001-T048 and T051-T064 are complete (62/64 tasks). Phase 7 uses eight CC BY 4.0 SimpleCube++ photographs
  and a CC-BY MIT fixed-scene pair under directional lights 0 and 24. Phase 8 automated,
  performance, documentation and demo preparation are complete.
- T049 remains open for a genuine second-student replay and independent five-minute workflow;
  it now also depends on T056 histogram evidence. T050 remains dependency-blocked by T049.
  Pending human evidence is not marked complete. Phase 9 histogram implementation and its
  panel-visible performance measurement are complete.
- Counts: Setup 4; Foundation 3; US1 14; US3 6; US2 5; US5 4; US4 8;
  Phase 8 baseline 4; US6 6; Final acceptance/review 2.
- Analysis remediation updated the specification, plan, contracts and traceability before T028.
  Phase 7 persistence, 20-run replay and comparison evidence is complete with explicit licensed
  provenance for every input and no synthetic image presented as photographed evidence.
- Research, data model, interface contracts and quickstart now define numeric behavior and field constraints;
  their presence is design evidence, not a substitute for running the planned tests.
