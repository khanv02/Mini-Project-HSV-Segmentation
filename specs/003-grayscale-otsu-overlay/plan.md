# Implementation Plan: Grayscale Segmentation, Otsu Assistance and Overlay Export

**Branch**: `[003-grayscale-otsu-overlay]` | **Date**: 2026-10-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-grayscale-otsu-overlay/spec.md`

## Summary

Add an explicit, opt-in grayscale segmentation path beside the existing default HSV path. The
new path validates exact grayscale eligibility, supports manual intensity thresholding and a
deterministic global Otsu threshold, then feeds the existing morphology, analysis, Watershed,
evaluation and preview pipeline with the same binary-mask contract. Add Save Overlay by composing
and exporting an immutable source-sized RGB snapshot of the exact active overlay variant. Extend
experiment evidence through a backward-compatible schema version without changing schema 1/2 or
the meanings of Save Mask and Save Result.

## Technical Context

**Language/Version**: Python >=3.11

**Primary Dependencies**: NumPy 2.x, Pillow 11-12, OpenCV 4.x, Tkinter from the Python standard library

**Storage**: Local lossless PNG, NumPy label arrays and versioned JSON experiment records; no database

**Testing**: pytest 8-9 with unit and integration suites, analytical NumPy fixtures and retained benchmark evidence

**Target Platform**: Offline Windows desktop application; processing core remains platform-neutral Python

**Project Type**: Single-package desktop application with independently testable processing and I/O layers

**Performance Goals**: For 100 Full-HD grayscale threshold edits, at least 95 current results within one second; GUI heartbeat checks no slower than 250 ms while work is pending

**Constraints**: HSV stays default; grayscale is explicit opt-in; no adaptive/local thresholding or automatic color-to-gray conversion; all processing and export identities are revision-safe; no new runtime dependency

**Scale/Scope**: One additional segmentation mode, one deterministic threshold algorithm, four overlay variants, existing image/video workflows, and experiment schema version 3

## Constitution Check

*GATE: Passed before Phase 0 research and passed again after Phase 1 design.*

| Principle | Gate result | Design evidence |
|---|---|---|
| I. Correctness before convenience | PASS | Exact eligibility and threshold boundaries are specified; Otsu ties and constant images have deterministic outcomes; pixel-exact tests are planned. |
| II. Modular architecture | PASS | `processing/grayscale.py` owns pure algorithms; application owns revision flow; GUI owns controls; I/O owns export and records. |
| III. Simplicity and readability | PASS | One global Otsu implementation, one settings model and existing mask contracts are reused; no framework or dependency is added. |
| IV. Automated tests and reproducible experiments | PASS | Analytical fixtures, stale-result tests, overlay pixel comparison, schema/replay tests and benchmark evidence are required. |
| V. Strict scope and academic integrity | PASS | Adaptive thresholding, automatic conversion and ML remain excluded; documentation states limitations and separates evaluation from visual judgment. |
| VI. Presentation and documentation quality | PASS | GUI status, a Vietnamese tutorial, algorithm notes, quickstart and acceptance evidence are planned. |
| VII. HSV core and backward compatibility | PASS | Every source opens in HSV mode; opt-in grayscale applies only to exactly eligible pixels; existing HSV models, exports and schema 1/2 semantics remain valid. |
| VIII. Explicit configuration and honest state | PASS | Mode, polarity, threshold source, resolved threshold, availability and overlay identity are explicit immutable data. |
| IX. Preserve current Python architecture | PASS | Changes extend existing `models`, `processing`, `application`, `io` and `gui` layers instead of introducing a parallel application. |
| X. Feature acceptance criteria | PASS | The feature spec defines independent stories, edge cases and measurable outcomes; the quickstart maps them to executable checks. |

The opt-in grayscale branch is a justified extension to the HSV-focused project: it does not
silently replace HSV, is limited to exact grayscale sources, and remains compatible with the
same downstream binary-mask pipeline. There are no constitution violations requiring an exception.

## Project Structure

### Documentation (this feature)

```text
specs/003-grayscale-otsu-overlay/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- processing.md
|   |-- desktop-workflow.md
|   |-- export.md
|   `-- experiment-record.md
`-- tasks.md
```

### Source Code (repository root)

```text
src/hsv_segmentation/
|-- models.py                         # Extend immutable request/result/settings snapshots
|-- processing/
|   |-- grayscale.py                 # New eligibility, manual threshold and Otsu core
|   `-- visualization.py             # Exact overlay snapshot composition
|-- application/
|   |-- session.py                   # Route HSV/grayscale masks through shared downstream stages
|   |-- processing_worker.py         # Cache source-derived grayscale/Otsu data and reject stale work
|   `-- playback.py                  # Carry mode/settings through video-frame requests
|-- io/
|   |-- export.py                    # Lossless immutable Overlay export
|   `-- experiments.py               # Backward-compatible schema 3 evidence
`-- gui/
    |-- grayscale_controls.py        # New compact mode, polarity and Otsu controls
    |-- controller.py                # Eligibility, revision, export and async orchestration
    |-- main_window.py               # Wire controls and expose current overlay snapshot
    `-- hsv_histogram.py             # Intensity presentation and Hue-unavailable state

tests/
|-- unit/
|   |-- test_grayscale.py
|   |-- test_models.py
|   |-- test_visualization.py
|   `-- test_export.py
`-- integration/
    |-- test_grayscale_session.py
    |-- test_grayscale_ui.py
    |-- test_export_session.py
    |-- test_extended_experiments.py
    |-- test_experiment_reproduction.py
    `-- test_playback.py

scripts/
`-- benchmark_gui_performance.py

docs/
|-- features/
|-- tutorials/
`-- verification/
```

**Structure Decision**: Extend the current single Python package and its layer boundaries. The
new algorithm is a pure processing module; no Tk type crosses into processing or I/O. Existing
`SegmentationResult` remains the downstream hand-off so morphology, analysis, evaluation and
video reuse their present behavior. Overlay pixels are composed by processing code, captured by
the controller and written by I/O rather than being read back from a Tk widget.

## Phase 0: Research Outcome

All technical unknowns were resolved in [research.md](./research.md). The selected approach uses
a 256-bin deterministic Otsu implementation, exact channel-equality eligibility, a discriminated
segmentation-mode model, immutable overlay snapshots and additive experiment schema version 3.
No `NEEDS CLARIFICATION` markers remain.

## Phase 1: Design Outcome

- [data-model.md](./data-model.md) defines settings, outcomes, snapshots, validation and state transitions.
- [processing.md](./contracts/processing.md) defines pure algorithm boundaries and exact numeric rules.
- [desktop-workflow.md](./contracts/desktop-workflow.md) defines GUI behavior, revisions and recoverable states.
- [export.md](./contracts/export.md) defines immutable lossless overlay publication.
- [experiment-record.md](./contracts/experiment-record.md) defines schema 3 and compatibility rules.
- [quickstart.md](./quickstart.md) defines the implementation verification and demonstration flow.

The post-design constitution re-check remains PASS: no new dependency, storage system, process,
unbounded queue or architecture layer was introduced.
