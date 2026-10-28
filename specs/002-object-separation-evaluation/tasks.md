# Tasks: HSV Object Analysis, Separation and Evaluation

**Input**: Design artifacts in `specs/002-object-separation-evaluation/`.
**Prerequisites**: spec.md, plan.md, research.md, data-model.md and contracts/.
**Tests**: Mandatory per user request and constitution. Tasks remain unimplemented.
**Organization**: Story slices with tests first, then algorithms, application and GUI integration.

## Format: `[ID] [P?] [Story] Description`

`[P]` means parallel only after listed dependencies complete and with no shared-file edits.
Every entry includes dependencies, acceptance and verification. Paths are repository-relative.
New files are proposals identified in plan.md. Keep all original feature-001 task IDs/statuses.

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Capture the baseline environment and regression outcome in `docs/verification.md`.
  **Depends**: none. **Acceptance**: actual interpreter/dependency versions, full-suite outcome
  and unchanged baseline outputs recorded; old evidence preserved. **Verify**: run
  `uv run --locked --extra test pytest -q`; record failures/skips honestly before implementation.
- [ ] T002 Create analytical fixture builders in `tests/fixtures/analysis_cases.py`.
  **Depends**: T001. **Acceptance**: rectangles/noise, diagonal pixels, holes, border/thin/full/
  empty masks, touching disks and partial-overlap truth have hand-derived counts/geometry;
  deterministic inputs and two-seed reference settings documented. **Verify**: inspect generated
  arrays against exact coordinates and expected TP=2,FP=1,FN=1; no file/network side effects.

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T003 Add settings/result/truth models to `src/hsv_segmentation/models.py` and validation
  cases to `tests/unit/test_models.py`.
  **Depends**: T002. **Acceptance**: data-model.md constraints enforced: connectivity integer
  in {4,8}; min_area_px nonnegative integer; seed_fraction finite real strictly between 0 and 1;
  background_iterations integer 0..10; kernel_size integer in {3,5,7,9}; truth threshold integer
  0..254; reject boolean numeric settings. Preserve positional field order/default behavior;
  new arrays immutable, count/shape invariants checked. **Verify**: model tests plus old constructor
  and mutation cases; new model tests fail before implementation then pass.
- [ ] T004 Consolidate orchestration without adding algorithms in
  `src/hsv_segmentation/application/processing_worker.py` and `application/session.py`.
  **Depends**: T003. **Acceptance**: cached processor delegates to process_source with cached
  HSV/histogram; current baseline exact pixels/cache reuse preserved; no circular imports.
  **Verify**: existing `tests/integration/test_image_session.py`, `test_histogram_panel.py` and
  `test_playback.py`, comparing cached/uncached masks and histogram identity.

## Phase 3: User Story 1 - Connected Regions (Priority: P1), MVP

**Goal**: Complete component analysis and filtering as an independently useful GUI slice.
**Independent Test**: D1 has exact region statistics/overlays, including empty and noise cases.

- [ ] T005 [P] [US1] Write analytical component/contour tests in `tests/unit/test_object_analysis.py`.
  **Depends**: T004. **Acceptance**: 4/8 connectivity, area equality, holes, thin/single pixels,
  bounds, centroids, external contours, stable IDs, immutability and invalid input covered.
  **Verify**: targeted pytest initially fails because proposed algorithm is absent.
- [ ] T006 [US1] Implement components/contours in `src/hsv_segmentation/processing/object_analysis.py`.
  **Depends**: T005. **Acceptance**: analyze_components/analyze_labels meet processing contract;
  background excluded; exact pixel statistics; contours associated with labels; no Tk/I/O.
  **Verify**: T005 tests pass; include holed region whose polygon area differs from pixel area.
- [ ] T007 [US1] Implement minimum-area filtering in `src/hsv_segmentation/processing/object_analysis.py`.
  **Depends**: T006. **Acceptance**: area >= minimum retained; raw/retained counts distinct;
  stable filtered labels/prediction; baseline unchanged; high minimum produces empty result.
  **Verify**: 1/4/9-pixel fixture with minimum 4 retains exactly 4 and 9; minimum 0 retains all.
- [ ] T008 [P] [US1] Add pure contour/box composition to `src/hsv_segmentation/processing/visualization.py`
  and tests to `tests/unit/test_visualization.py`.
  **Depends**: T007. **Acceptance**: independently toggled annotations on source copy; correct
  source coordinates; original arrays unchanged. **Verify**: exact known box pixels and
  immutability tests with single-pixel/border cases.
- [ ] T009 [US1] Integrate analysis settings/revisions into `src/hsv_segmentation/application/session.py`,
  `application/processing_worker.py`, `application/playback.py` and `gui/controller.py`.
  **Depends**: T007. **Acceptance**: new settings reach image open, threshold edits, video open,
  next, paused reprocess and restart; synchronous/cached equality; stale settings results rejected.
  **Verify**: add/run delayed-worker and image/video cases in `tests/integration/test_analysis_session.py`.
- [ ] T010 [US1] Add basic analysis controls/table in `src/hsv_segmentation/gui/analysis_panel.py`
  and integrate `gui/main_window.py`/`gui/controller.py`.
  **Depends**: T008,T009. **Acceptance**: enabled state, connectivity, minimum area, raw/retained
  counts, region statistics, contour/box toggles and semantic disclaimer; default-disabled;
  source sampling and three previews preserved. **Verify**: automated D1 controls/geometry,
  zoom/ROI and empty-state checks in `tests/integration/test_analysis_ui.py`.

**Checkpoint**: US1 is independently usable without Watershed, ground truth or schema 2.

## Phase 4: User Story 2 - Watershed Separation (Priority: P2)

**Goal**: Optional separation with explicit status and baseline comparison.
**Independent Test**: D2 yields two reference labels and graceful inadequate-marker behavior.

- [ ] T011 [P] [US2] Write marker/separation tests in `tests/unit/test_watershed.py`.
  **Depends**: T004. **Acceptance**: known two seeds, empty/full/tiny/no-background/one-seed,
  parameter validation, domain clipping, ridge exclusion and source immutability covered.
  **Verify**: tests fail before implementing separation; reference fixture demonstrably has two seeds.
- [ ] T012 [US2] Implement distance transform/markers in `src/hsv_segmentation/processing/watershed.py`.
  **Depends**: T011. **Acceptance**: explicit L2/5 distance, zero-padding/cropping, strict seed
  fraction, configured expansion; marker values 0/1/2+ and >=2 foreground-seed guard.
  **Verify**: marker tests inspect shapes, positive seed count and expected not-applied reasons.
- [ ] T013 [US2] Complete constrained separation and label statistics in
  `src/hsv_segmentation/processing/watershed.py`.
  **Depends**: T012,T007. **Acceptance**: BGR/markers copied; watershed ridges separated; results
  constrained to baseline; analyze_labels filters after splitting without reconnecting regions;
  applied/empty/not_applied contract honored. **Verify**: full T011 tests, two distinct labels,
  binary union/ridge invariants and deterministic repeated runs in same environment.
- [ ] T014 [US2] Wire Watershed through `src/hsv_segmentation/application/session.py`,
  `application/processing_worker.py`, `application/playback.py` and `gui/controller.py`.
  **Depends**: T013,T009. **Acceptance**: every image/video path has matching separation settings;
  invalid/late settings do not commit; disabling restores exact baseline output.
  **Verify**: extend `tests/integration/test_analysis_session.py` with delayed toggles/frame changes.
- [ ] T015 [US2] Add Watershed controls/comparison to `src/hsv_segmentation/gui/analysis_panel.py`,
  `gui/main_window.py` and `gui/controller.py`.
  **Depends**: T014,T010. **Acceptance**: switch, valid marker settings, status/reason, labeled
  boundaries/regions and baseline comparison; unavailable target never silently falls back.
  **Verify**: extend `tests/integration/test_analysis_ui.py` for D2, disable/restore and failure status.

## Phase 5: User Story 3 - IoU and Dice (Priority: P2)

**Goal**: Evaluate named binary predictions against explicitly bound ground truth.
**Independent Test**: D3 exact partial/empty cases work using baseline without Watershed.

- [ ] T016 [P] [US3] Write overlap/empty-case tests in `tests/unit/test_evaluation.py`.
  **Depends**: T004. **Acceptance**: identical/disjoint/partial/both-empty/one-empty, TP/FP/FN/TN,
  shape/dtype/binary validation, large denominator safety and immutability covered.
  **Verify**: fail first, including IoU=0.5 and Dice=2/3 with tolerance 1e-12.
- [ ] T017 [US3] Implement pure scores in `src/hsv_segmentation/processing/evaluation.py`.
  **Depends**: T016. **Acceptance**: processing contract, finite [0,1] scores, explicit empty
  statuses and Python-integer denominator counts; no GUI/I/O. **Verify**: all T016 tests pass.
- [ ] T018 [P] [US3] Implement truth adapter and decoding tests in
  `src/hsv_segmentation/io/ground_truth.py` and `tests/integration/test_ground_truth.py`.
  **Depends**: T003. **Acceptance**: PNG/BMP 1/L/LA/palette/equal-RGB/RGBA rules; strict > threshold;
  original/pixel hashes; no rotation/resize; reject JPEG, unequal channels, unsupported depths,
  mismatches and corruption. **Verify**: generated file matrix at threshold 0 and 254, boundary
  values, alpha disclosure and typed errors; no changes to generic source-image loader behavior.
- [ ] T019 [P] [US3] Add TP/FP/FN visualization in `src/hsv_segmentation/processing/visualization.py`
  with `tests/unit/test_visualization.py` coverage.
  **Depends**: T017,T008. **Acceptance**: distinct legend mapping, exact region classification,
  source preserved; composition skipped when hidden. **Verify**: known confusion fixture counts/colors.
- [ ] T020 [US3] Add truth/target state and revision handling in
  `src/hsv_segmentation/application/session.py`, `application/processing_worker.py`,
  `application/playback.py` and `gui/controller.py`.
  **Depends**: T017,T018,T014. **Acceptance**: pause/load binding, clear/load revision, target
  selection; retain truth for same-frame edits; clear on advance/restart/source replacement;
  unavailable/not-applied targets yield no metric. **Verify**: delayed-load/clear/frame/threshold
  races in `tests/integration/test_analysis_session.py`; cached/uncached evaluation agreement.
- [ ] T021 [US3] Integrate evaluation UI in `src/hsv_segmentation/gui/analysis_panel.py`,
  `gui/main_window.py` and `gui/controller.py`.
  **Depends**: T019,T020,T015. **Acceptance**: Load/Clear Truth, conversion threshold, target,
  provenance, pending/empty states, IoU/Dice and confusion legend; coverage never called accuracy.
  **Verify**: D3 and D4 tests in `tests/integration/test_analysis_ui.py`; cancellation/error recovery.

## Phase 6: User Story 4 - Extended Recording (Priority: P3)

**Goal**: Publish/replay derived evidence without changing legacy records.
**Independent Test**: Baseline schema 1 and extended schema 2 reconstruct exact saved predictions.

- [ ] T022 [P] [US4] Write schema/publication tests in `tests/integration/test_extended_experiments.py`.
  **Depends**: T003. **Acceptance**: schema-1 compatibility; schema-2 optional status/evaluation,
  label and normalized-truth artifacts/hashes; write-failure and captured-frame checks.
  **Verify**: tests fail before extending publisher, using injected failures and delayed writes.
- [ ] T023 [US4] Extend publisher in `src/hsv_segmentation/io/experiments.py`.
  **Depends**: T022,T020. **Acceptance**: exact experiment-record contract; baseline keys/artifacts
  unchanged; optional schema 2, int32 label hash, no-pickle label file; artifacts before atomic
  record publication; partial failure never reports complete run. **Verify**: T022 tests and
  existing `tests/integration/test_experiment_records.py`.
- [ ] T024 [US4] Integrate immutable recording snapshot and controls in
  `src/hsv_segmentation/gui/controller.py` and `gui/experiment_panel.py`.
  **Depends**: T023,T021. **Acceptance**: pending/invalid target blocked; captured source/frame/
  settings/truth cannot drift; duplicate writes disabled; success/failure path actionable.
  **Verify**: delayed publication, source replacement and failed-artifact UI cases in
  `tests/integration/test_extended_experiments.py` and existing export-session tests.
- [ ] T025 [US4] Add versioned replay support to `scripts/generate_experiment_evidence.py` and
  `tests/integration/test_experiment_reproduction.py`.
  **Depends**: T023. **Acceptance**: versions 1/2 dispatched, unknown version rejected; verify
  source/frame/environment/artifact hashes; exact derived counts/labels and score tolerance
  1e-12; normalized truth sufficient if original truth file absent. **Verify**: replay temporary
  new records and existing retained runs without regenerating/rewriting legacy evidence.

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T026 Harden integrated failure/layout behavior in `tests/integration/test_analysis_ui.py`,
  `test_analysis_session.py` and `test_error_recovery.py`, fixing affected existing modules.
  **Depends**: T024,T025. **Acceptance**: all four stories' image/video/stale/close/resource
  cases pass; at 960x640 and large desktop three previews >=160x120, histogram shown/hidden;
  keyboard/sampling/presets remain usable. **Verify**: focused integration suite plus walkthrough;
  no skipped GUI check is recorded as passed.
- [ ] T027 [P] Extend performance measurement in `scripts/benchmark_gui_performance.py`.
  **Depends**: T026. **Acceptance**: separate baseline/analysis/Watershed modes over 100 edits;
  baseline >=95/100 <=1s; >=95/100 UI heartbeats <=250ms while pending; report median/p95,
  process peak-memory measurement method/environment and exact current-result identity.
  **Verify**: execute on documented computer, store new files under `experiments/feature-002/`;
  never overwrite baseline evidence; investigate unmet acceptance before completion.
- [ ] T028 [P] Update feature explanations and demo procedure in `README.md`, `docs/algorithm.md`,
  `docs/acceptance.md` and `docs/implementation-stages.md`.
  **Depends**: T026. **Acceptance**: D1-D5, all settings/units/defaults, truth format/empty rules,
  schema compatibility, pixel-area vs contour-area, Watershed limitations and coverage wording
  documented; examples match delivered GUI. **Verify**: execute quickstart.md walkthrough against docs.
- [ ] T029 Record final requirement/evidence matrix in `docs/verification.md` and
  `experiments/feature-002/report.md`.
  **Depends**: T027,T028. **Acceptance**: every FR/NFR/SC has actual automated/manual outcome,
  command, environment and evidence; D1-D5 evidence and one extended run per story retained;
  legacy pending human acceptance remains explicit. **Verify**: full pytest suite, artifact/replay
  checks, performance results and matrix audit; no inference of feature completion from checklist.
- [ ] T030 Review completion against constitution and design in
  `specs/002-object-separation-evaluation/tasks.md`.
  **Depends**: T029. **Acceptance**: all required checks pass, no unrecorded exceptions/new
  dependencies; application architecture preserved; check boxes only with linked evidence.
  **Verify**: review git diff, full test result and FR/NFR/SC matrix; unresolved checks remain open.

## Dependencies & Execution Order

Default: T001-T004 -> components/contours -> area filter -> Watershed -> evaluation -> final
GUI integration -> recording/replay -> cross-story tests -> documentation/demonstrations.
Unit tests accompany each algorithm; do not defer all testing until integration. US1 includes a
minimal GUI slice so the MVP is usable independently; later stories extend the same panel.

```text
T001 -> T002 -> T003 -> T004
T004 -> T005 -> T006 -> T007 -> T008
T007 -> T009 -> T010 (also T008)
T004 -> T011 -> T012 -> T013 (also T007) -> T014 (also T009) -> T015 (also T010)
T004 -> T016 -> T017 -> T019 (also T008)
T003 -> T018
T017,T018,T014 -> T020 -> T021 (also T019,T015)
T003 -> T022; T022,T020 -> T023 -> T025
T023,T021 -> T024; T024,T025 -> T026 -> T027,T028 -> T029 -> T030
```

Shared application/controller/model/UI files must have a single integration owner. Parallel
algorithm work is possible after stable T003/T004 contracts; merge shared-file tasks sequentially.
US3 pure evaluation has no dependency on Watershed; only target-selector integration joins later.

## Parallel Examples

- US1: T008 annotations and T009 application integration after T007 (different files).
- US2: T011/T012 can proceed alongside US1 work after T004; T013 waits for analyze_labels/T007.
- US3: T016/T017 and T018 can proceed independently after their prerequisites; T019 must wait
  for T008 to avoid editing visualization.py concurrently.
- US4: T022 test authoring may run while other stories progress after T003; T025 replay can run
  beside T024 GUI recording once T023 is complete.
- Final: T027 performance tooling and T028 documentation after T026, with separate files.

## Requirement Traceability

| Requirements | Tasks | Acceptance evidence |
| --- | --- | --- |
| FR-001, NFR-006 | T001,T003,T004,T009,T014,T026 | Default-disabled regression and baseline export equality |
| FR-002..004, SC-001 | T005..010 | Analytical component/filter/contour and GUI D1 checks |
| FR-005..006, SC-002 | T011..015 | Marker, confinement, status and comparison D2 checks |
| FR-007 | T018,T020,T021 | Lossless truth format/normalization/binding matrix |
| FR-008..010, SC-003 | T016..021 | Reference counts/scores and D3 UI/confusion checks |
| FR-011..012, SC-004 | T009,T014,T020,T024,T026 | Delayed source/settings/truth/frame and recording checks |
| FR-013, SC-005 | T022..025,T029 | Schema 1/2 publication, replay and hashes |
| FR-014 | T011,T018,T020,T026 | Expected status and recovery message/state tests |
| NFR-001..002, NFR-005 | T003..025,T030 | Offline/pure algorithms, deterministic counts/labels/tests |
| NFR-003, SC-006 | T027,T029 | Separate baseline/extension timing, heartbeat and memory evidence |
| NFR-004 | T010,T015,T021,T026 | Minimum geometry, focus and histogram visibility checks |

## Implementation Strategy

Deliver US1 first as MVP. Validate exact region measurements before adding optional separation.
Deliver US2 and independent US3 algorithms next; integrate the shared GUI in the listed order.
Add US4 after snapshots and truth binding stabilize. Finish with cross-story regressions,
measured performance and honest documented demonstrations. No implementation task is completed
by creation of this SDD; all 30 checkboxes start open.
