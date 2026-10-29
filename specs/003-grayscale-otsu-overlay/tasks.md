# Tasks: Grayscale Segmentation, Otsu Assistance and Overlay Export

**Input**: Design documents from `/specs/003-grayscale-otsu-overlay/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required by the feature specification and project constitution. Within every story,
create the listed tests first, run them to confirm the missing behavior fails, then implement.

**Organization**: Tasks are grouped by user story so manual grayscale segmentation is an MVP and
Otsu, Overlay export and reproducible evidence remain independently verifiable increments.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: May run in parallel because it changes different files and has no incomplete dependency.
- **[USn]**: Maps the task to a user story from `spec.md`.
- Every task includes concrete repository paths.

## Phase 1: Setup (Shared Test Infrastructure)

**Purpose**: Establish deterministic fixtures without adding opaque binary test assets.

- [X] T001 Add generated exact-gray, nearly-gray, two-level, constant and Full-HD fixture factories with expected masks to `tests/conftest.py`
- [X] T002 [P] Add Feature 003 acceptance-evidence headings and command/result placeholders to `docs/verification/feature-003-grayscale-otsu-overlay.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define common immutable identities before any story changes processing or the GUI.

**CRITICAL**: Complete this phase before implementing any user story.

- [X] T003 Write failing validation/default/immutability tests for `SegmentationMode`, `GrayscaleSettings`, `GrayscaleEligibility`, `OtsuOutcome`, `OverlayDisplaySettings`, and `OverlaySnapshot` in `tests/unit/test_models.py`
- [X] T004 Implement the shared Feature 003 value objects, immutable-array ownership, cross-field validation and HSV-compatible defaults in `src/hsv_segmentation/models.py`
- [X] T005 Write failing backward-compatibility tests proving existing HSV `ProcessingRequest` and `SegmentationResult` construction and identities remain unchanged in `tests/unit/test_models.py`
- [X] T006 Thread default mode/settings through `ProcessingRequest` and `SegmentationResult` construction without changing HSV output in `src/hsv_segmentation/application/session.py`, `src/hsv_segmentation/application/processing_worker.py`, and `src/hsv_segmentation/application/playback.py`
- [X] T007 Run the existing model, session, worker and playback tests and record the pre-story compatibility result in `docs/verification/feature-003-grayscale-otsu-overlay.md`

**Checkpoint**: Common models are immutable and existing HSV flows still pass before grayscale behavior is added.

---

## Phase 3: User Story 1 - Segment a Grayscale Image by Intensity (Priority: P1) MVP

**Goal**: Let a user explicitly select eligible grayscale pixels with one manual threshold and a
visible bright/dark polarity while HSV remains the default.

**Independent Test**: Open an exact-gray fixture, enter Grayscale, verify `> T` and `<= T` masks
pixel-for-pixel, then reject a one-pixel nearly-gray fixture without changing the current HSV result.

### Tests for User Story 1

- [X] T008 [P] [US1] Write failing unit tests for exact RGB eligibility, one-pixel ineligibility, threshold boundaries `0/255`, bright/dark complementarity, input validation and non-mutation in `tests/unit/test_grayscale.py`
- [X] T009 [P] [US1] Write failing processing integration tests for manual grayscale masks flowing through morphology, analysis and evaluation while HSV output remains unchanged in `tests/integration/test_grayscale_session.py`
- [X] T010 [P] [US1] Write failing controller/UI tests for HSV default, eligible opt-in, ineligible rejection, editable integer threshold, visible polarity, Hue-unavailable state and four synchronized previews in `tests/integration/test_grayscale_ui.py`
- [X] T011 [P] [US1] Write failing image/video request identity tests for mode, settings and stale manual completions in `tests/integration/test_playback.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement pure exact-channel eligibility, intensity extraction and manual `bright > T` / `dark <= T` mask generation in `src/hsv_segmentation/processing/grayscale.py`
- [X] T013 [US1] Add mode-aware original-mask generation and shared downstream stage reuse in `src/hsv_segmentation/application/session.py`
- [X] T014 [US1] Cache source-derived eligibility/intensity and carry mode/settings revisions through bounded processing in `src/hsv_segmentation/application/processing_worker.py` and `src/hsv_segmentation/application/playback.py`
- [X] T015 [P] [US1] Implement compact accessible mode, manual threshold and polarity controls with explicit eligible/ineligible status in `src/hsv_segmentation/gui/grayscale_controls.py`
- [X] T016 [US1] Wire source reset, opt-in rejection, settings revisions and result commits in `src/hsv_segmentation/gui/controller.py`
- [X] T017 [US1] Integrate the controls and mode-aware labels without reducing the four-preview workspace in `src/hsv_segmentation/gui/main_window.py`
- [X] T018 [US1] Present intensity/Value in grayscale mode and mark Hue unavailable while preserving normal HSV histograms in `src/hsv_segmentation/gui/hsv_histogram.py`
- [X] T019 [P] [US1] Write the Vietnamese grayscale-versus-binary, manual threshold and polarity guide in `docs/features/grayscale-segmentation.md` and `docs/tutorials/grayscale-manual.md`
- [X] T020 [US1] Run the US1 focused commands from `specs/003-grayscale-otsu-overlay/quickstart.md` and record exact-mask and three-minute-demo evidence in `docs/verification/feature-003-grayscale-otsu-overlay.md`

**Checkpoint**: Manual Grayscale Mode is a complete independently demonstrable MVP; no Otsu or Overlay export is required.

---

## Phase 4: User Story 2 - Use Otsu as an Optional Threshold Suggestion (Priority: P2)

**Goal**: Compute one deterministic global threshold for an eligible current grayscale snapshot,
report its provenance and preserve valid state when no meaningful split exists.

**Independent Test**: Resolve a known two-level/tied fixture repeatedly, verify the smallest optimal
threshold and exact mask, reject a constant fixture, then return to the preserved manual value.

### Tests for User Story 2

- [X] T021 [P] [US2] Write failing Otsu unit tests for analytical histograms, smallest-threshold ties, both polarities, constant images, invalid arrays, determinism and non-mutation in `tests/unit/test_grayscale.py`
- [X] T022 [P] [US2] Write failing session/worker tests for applied and unavailable outcomes, last-valid-result preservation and stale source/settings completions in `tests/integration/test_grayscale_session.py`
- [X] T023 [P] [US2] Write failing paused-video tests for current-frame Otsu identity and frame-change rejection in `tests/integration/test_playback.py`
- [X] T024 [P] [US2] Write failing UI tests for computed-threshold labeling, polarity, disabled Otsu on ineligible sources, unavailable explanations and restoration of manual editing in `tests/integration/test_grayscale_ui.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement the 256-bin between-class-variance Otsu algorithm, smallest-optimum tie rule and explicit unavailable outcome in `src/hsv_segmentation/processing/grayscale.py`
- [X] T026 [US2] Resolve Otsu within the mode-aware session without fabricating a result and propagate outcome identity in `src/hsv_segmentation/application/session.py`
- [X] T027 [US2] Schedule/cancel Otsu through the existing bounded worker and enforce request/settings/frame revision commits in `src/hsv_segmentation/application/processing_worker.py` and `src/hsv_segmentation/application/playback.py`
- [X] T028 [US2] Add Manual/Otsu selection, pending/applied/unavailable state and threshold provenance to `src/hsv_segmentation/gui/grayscale_controls.py` and `src/hsv_segmentation/gui/controller.py`
- [X] T029 [P] [US2] Write the Vietnamese Otsu explanation, bimodal assumption, constant-image behavior and uneven-light limitation in `docs/features/otsu-threshold.md` and extend `docs/tutorials/grayscale-manual.md`
- [X] T030 [US2] Run the US2 focused commands from `specs/003-grayscale-otsu-overlay/quickstart.md` and record threshold/tie/constant/video evidence in `docs/verification/feature-003-grayscale-otsu-overlay.md`

**Checkpoint**: Otsu is optional, deterministic and independently testable; Manual remains usable and HSV stays default.

---

## Phase 5: User Story 3 - Save the Current Overlay (Priority: P2)

**Goal**: Save exact source-resolution pixels for the overlay variant visible when export begins,
without changing Save Mask or Save Result.

**Independent Test**: Capture and save segmentation, object-analysis, Watershed and confusion
variants, decode each PNG and require exact equality to its immutable snapshot during UI changes.

### Tests for User Story 3

- [X] T031 [P] [US3] Write failing pure composition tests for variant selection, required data, source dimensions, immutable ownership and deterministic pixels in `tests/unit/test_visualization.py`
- [X] T032 [P] [US3] Write failing Overlay PNG tests for exact decoded pixels, receipt identity, cancellation boundary, overwrite and atomic failure cleanup while retaining Mask/Result semantics in `tests/unit/test_export.py`
- [X] T033 [P] [US3] Write failing controller integration tests for Save Overlay availability, all four variants, source/frame/display/truth changes during I/O, completion messaging and video pause/resume in `tests/integration/test_export_session.py`

### Implementation for User Story 3

- [X] T034 [US3] Implement validated active-variant selection and immutable `OverlaySnapshot` composition using existing primitives in `src/hsv_segmentation/processing/visualization.py`
- [X] T035 [US3] Add atomic `save_overlay_png`/Overlay snapshot export and variant-aware receipt data without changing existing kinds in `src/hsv_segmentation/io/export.py`
- [X] T036 [US3] Make `src/hsv_segmentation/gui/main_window.py` display pixels from the same overlay composition contract and expose its current display settings/variant
- [X] T037 [US3] Add Save Overlay destination, overwrite, immutable capture, worker submission, stale-safe completion and availability handling in `src/hsv_segmentation/gui/controller.py`
- [X] T038 [P] [US3] Write the Vietnamese Result-versus-Overlay and export-variant guide in `docs/features/overlay-export.md` and `docs/tutorials/save-overlay.md`
- [X] T039 [US3] Run the US3 focused commands from `specs/003-grayscale-otsu-overlay/quickstart.md` and record pixel equality plus race/failure evidence in `docs/verification/feature-003-grayscale-otsu-overlay.md`

**Checkpoint**: Every supported Overlay variant is losslessly exportable from an immutable exact-pixel snapshot.

---

## Phase 6: User Story 4 - Reproduce Grayscale and Overlay Evidence (Priority: P3)

**Goal**: Retain enough versioned evidence to reproduce manual/Otsu masks and verify optional
Overlay pixels while preserving existing HSV schema 1/2 interpretation.

**Independent Test**: Publish manual and Otsu schema 3 runs, reconstruct their masks and overlay
hashes, then replay existing schema 1/2 HSV fixtures unchanged and reject unknown versions.

### Tests for User Story 4

- [X] T040 [P] [US4] Write failing schema-selection and record-validation tests for grayscale provenance, optional Overlay metadata/hashes, unchanged schema 1/2 and unknown-version rejection in `tests/integration/test_extended_experiments.py`
- [X] T041 [P] [US4] Write failing reproduction tests for manual masks, recomputed Otsu/tie rule, polarity, source/frame/settings identity, evidence drift and Overlay pixel hashes in `tests/integration/test_experiment_reproduction.py`
- [X] T042 [P] [US4] Write failing controller tests that capture one mutually consistent result/Overlay snapshot for experiment publication in `tests/integration/test_export_session.py`

### Implementation for User Story 4

- [X] T043 [US4] Implement additive schema 3 selection, segmentation provenance and optional atomic Overlay artifact/hash publication in `src/hsv_segmentation/io/experiments.py`
- [X] T044 [US4] Extend record loading/replay verification for schema 3 while preserving schema 1/2 behavior in `src/hsv_segmentation/io/experiments.py` and existing replay modules under `src/hsv_segmentation/application/`
- [X] T045 [US4] Capture mutually consistent experiment and Overlay snapshots and pass them through background publication in `src/hsv_segmentation/gui/controller.py`
- [X] T046 [P] [US4] Document schema 3 fields, manual/Otsu reproduction and Overlay integrity checks in `docs/features/experiments.md` and `docs/verification/feature-003-grayscale-otsu-overlay.md`
- [X] T047 [US4] Run the US4 focused commands from `specs/003-grayscale-otsu-overlay/quickstart.md` and retain reproduction plus legacy-record evidence in `docs/verification/feature-003-grayscale-otsu-overlay.md`

**Checkpoint**: Manual/Otsu/Overlay evidence is reproducible and legacy HSV records retain their meanings.

---

## Phase 7: Polish and Cross-Cutting Acceptance

**Purpose**: Verify combinations, performance, documentation navigation and complete regression.

- [X] T048 [P] Add combination coverage for grayscale with morphology, object analysis, Watershed, ground truth, evaluation targets and video in `tests/integration/test_grayscale_session.py`
- [X] T049 [P] Add the `grayscale-full-hd` 100-edit latency and pending-work heartbeat scenario with machine-readable output to `scripts/benchmark_gui_performance.py`
- [X] T050 Add Feature 003 navigation links and concise Vietnamese feature summariesâ€”without embedding the full tutorialsâ€”to `README.md` and the relevant indexes under `docs/`
- [X] T051 Run the Full-HD benchmark, require SC-007 thresholds, and retain environment plus raw result in `docs/verification/feature-003-grayscale-otsu-overlay.md`
- [X] T052 Run `uv run pytest -q`, record the complete regression result, and fix only Feature 003 regressions in the files named by the failing story tasks
- [X] T053 Audit FR-001..FR-021 and SC-001..SC-008 against tests/docs/evidence and complete the traceability table in `docs/verification/feature-003-grayscale-otsu-overlay.md`
- [X] T054 Perform the full Vietnamese quickstart demonstration from `specs/003-grayscale-otsu-overlay/quickstart.md`, verify the three-minute manual path and remove all evidence placeholders

---

## Dependencies and Execution Order

### Phase dependencies

```text
Phase 1 Setup
  -> Phase 2 Foundation
       -> Phase 3 US1 Manual Grayscale (MVP)
            -> Phase 4 US2 Otsu
       -> Phase 5 US3 Save Overlay
       -> Phase 6 US4 Evidence (requires delivered grayscale and Overlay models)
            -> Phase 7 Polish and Acceptance
```

- Phase 1 has no dependency.
- Phase 2 depends on generated fixtures and blocks all user stories.
- US1 depends only on Foundation and is the MVP.
- US2 depends on the manual grayscale processing path from US1.
- US3 depends only on Foundation and current pre-feature overlay primitives, so it can proceed in
  parallel with US1/US2 after the common snapshot models exist.
- US4 depends on completed grayscale provenance from US1/US2 and Overlay snapshot/export from US3.
- Polish starts after all selected stories are complete.

### Within-story order

1. Write the story's failing tests and confirm they fail for the missing behavior.
2. Implement pure processing/models before application orchestration.
3. Implement application orchestration before GUI wiring or I/O publication.
4. Run the focused story tests and complete its verification checkpoint.
5. Do not weaken old tests or silently change HSV, Mask, Result or schema 1/2 semantics.

## Parallel Opportunities

- T002 can run beside T001; T008-T011 are independent test files.
- After T014, T015 and T019 can proceed independently while controller integration is prepared.
- T021-T024 can be authored in parallel; T029 is independent of code implementation.
- US3 can start after Foundation while US1/US2 processing work continues because it uses separate
  visualization/export files; T031-T033 and T038 are parallel candidates.
- T040-T042 can be authored in parallel; T046 can proceed once the schema contract is stable.
- T048 and T049 can run in parallel before the final sequential acceptance tasks.

## Parallel Examples

### User Story 1

```text
T008: Pure eligibility/manual threshold tests in tests/unit/test_grayscale.py
T009: Processing integration tests in tests/integration/test_grayscale_session.py
T010: UI behavior tests in tests/integration/test_grayscale_ui.py
T011: Playback identity tests in tests/integration/test_playback.py
```

### User Story 3

```text
T031: Overlay composition tests in tests/unit/test_visualization.py
T032: Overlay file publication tests in tests/unit/test_export.py
T033: Controller race tests in tests/integration/test_export_session.py
T038: Vietnamese Overlay documentation under docs/
```

## Implementation Strategy

### MVP first

1. Complete T001-T007 (Setup and Foundation).
2. Complete T008-T020 (US1).
3. Stop and validate exact masks, ineligible rejection, HSV default and the three-minute tutorial.
4. The result is a useful manual grayscale demo even before Otsu or Overlay export ships.

### Incremental delivery

1. Add US2 for deterministic Otsu comparison; validate constant and stale cases.
2. Add US3 for exact Overlay retention; validate every variant and export race.
3. Add US4 only after the producing snapshots are stable; validate schema compatibility.
4. Complete cross-cutting combinations, performance, README navigation and full regression.

## Notes

- `[P]` never means two tasks should edit the same file concurrently.
- Commit after each completed story/checkpoint or another coherent green-test group.
- Preserve unrelated untracked files and user changes.
- Do not add adaptive thresholding, automatic color conversion, ML or automatic mode selection.
- A visual result is not an accuracy claim; ground-truth metrics remain the evaluation mechanism.
