# Implementation Plan: HSV Color Segmentation

**Branch**: `main` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-hsv-color-segmentation/spec.md`.
The feature resolver reports `001-hsv-color-segmentation` as its logical feature identifier;
the checked-out Git branch is `main`. No branch was created or switched during planning.

## Summary

Build a local Windows desktop application for academic HSV color segmentation. Deliver the
still-image workflow first: open an image, edit six HSV bounds, and compare original, binary
mask, and extracted colors. Add video playback/frame exports, reliable file handling, and
recorded experiments across at least 10 images and 20 threshold configurations afterward.

Use vectorized NumPy float64 equations for the core RGB-to-HSV conversion and thresholding,
Tkinter/Pillow for presentation and image files, and OpenCV for sequential video decoding.
The algorithm accepts arrays and explicit parameters; it never imports the GUI or reads files.
All long processing and file operations run outside Tk event handlers, with bounded work and
revision checks before presenting results.

The upper hue control accepts 360 as an interval endpoint; lower hue remains 0..359.
Pixel hue remains in [0,360), so default hue bounds (0,360) select the entire hue domain.
This corrects the previously inconsistent (0,359) full-domain assumption without quantizing
pixels or adding a seventh control. The spec and tasks are synchronized with this decision.

## Technical Context

**Language/Version**: CPython 3.11, 64-bit Windows distribution with Tcl/Tk; record the exact
patch version in the locked demonstration environment during setup.

**Primary Dependencies**: NumPy (float64 array mathematics), Pillow (PNG/JPEG/BMP decoding,
display conversion, PNG writing), opencv-python (video capture only), pytest (test dependency),
and setuptools (packaging build dependency). Tkinter, colorsys, dataclasses, concurrent.futures,
queue, json, hashlib, pathlib, and uuid come from Python's standard library.
Select installable releases for this interpreter during T002 and pin their exact versions,
including build tools and transitive dependencies, in `requirements-lock.txt`. Do not claim
that dependency compatibility or a clean installation has already been tested during planning.

**Storage**: Local input files, lossless PNG outputs, per-run JSON metadata and a JSON environment
record. No database, remote storage, authentication, or backend service.

**Testing**: pytest unit and integration tests, hand-derived RGB/HSV cases, independent colorsys
comparisons, temporary-file round trips, deterministic playback doubles, real video smoke checks,
and a manual GUI/reproduction acceptance guide. Core tests require no GUI or input files.

**Target Platform**: Windows 10/11 x64; first verify the intended university machine and record
its OS, CPU, RAM, Python, Tcl/Tk, package versions and selected video backend. Other OSes are
not acceptance targets. Use the Windows CPython launcher rather than assuming the first
`python` on PATH is the desired installation.

**Project Type**: Single-package offline desktop application with module entry point
`python -m hsv_segmentation` and a `src/` package layout.

**Performance Goals**: For a 1920x1080 still image, at least 95 of 100 valid control changes
produce a rendered current result within one second after the final edit. Timing includes
coordination, processing, preview preparation and GUI rendering, rather than just mask creation.
No guaranteed real-time video frame rate. Playback may slow while preserving synchronization.

**Constraints**: Six numeric controls, source-resolution computation/export, inclusive comparisons,
no rounding before membership tests, no mutable global thresholds, no GUI calls from workers,
one serialized worker and one replaceable pending request, and no unbounded video buffering.
Start with a documented 12,000,000-pixel input/frame limit checked before allocation where
metadata permits; reject larger inputs clearly and catch allocation failures. This limit is a
project resource policy, not a claim that all smaller images fit every computer. Adjust only
with recorded resource measurements and corresponding documentation/tests.

**Scale/Scope**: One active media session; bounded previous and candidate source state during
opening; three visible previews; still-image exports and individual video-frame exports;
at least 10 distinct images, two settings per image, and one photographed scene under two
lighting conditions. No tracking, counting, ML, audio, seeking, or full-video encoding.

## Constitution Check

**Pre-research gate: PASS at design level.** The academic scope and intended separation have
no justified exceptions. Earlier placeholder gates are replaced by explicit checks below.
**Post-design gate: PASS at design level.** Research, data entities, contracts and validation
steps preserve each principle. These passes assess design, not unbuilt runtime behavior.

| Principle | Design constraint and validation evidence planned | Pre | Post |
| --- | --- | --- | --- |
| I. Correctness and clarity | Explicit float64 equations, units, endpoint rules; analytical and independent reference tests in processing contract | PASS | PASS |
| II. Modular architecture | One authoritative processing implementation; models/errors are shared leaves; no dependency cycles | PASS | PASS |
| III. GUI/processing/I/O separation | GUI delegates through application; processing consumes memory only; I/O owns paths/codecs | PASS | PASS |
| IV. Student maintainability | One package, stdlib desktop toolkit, four focused external packages including tests | PASS | PASS |
| V. Naming and clean code | snake_case modules, unit-bearing fields, documented constants, no speculative interfaces | PASS | PASS |
| VI. Independent core tests | Conversion, threshold validation, mask generation and extraction callable without Tk/files | PASS | PASS |
| VII. Tests and reproducibility | Exact mask tests, explicit conversion tolerances, locked environment, source hashes and 20 runs | PASS | PASS |
| VIII. Strict academic scope | No services/database; every dependency has a specific documented role in research.md | PASS | PASS |
| IX. Academic explanation | Equations, pipeline, parameter meanings, limitations and labeled experiment comparisons | PASS | PASS |

Acceptance review rechecks these gates after implementation. A missed acceptance result remains
open; it cannot be waived by marking this planning table PASS.

## Project Structure

### Documentation (this feature)

```text
specs/001-hsv-color-segmentation/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/
    processing.md
    desktop-workflow.md
    experiment-record.md
  checklists/requirements.md
  tasks.md
```

### Source Code (repository root)

```text
pyproject.toml
requirements-lock.txt
README.md
src/hsv_segmentation/
  __init__.py
  __main__.py
  models.py
  errors.py
  processing/
    __init__.py
    color.py
    thresholds.py
    segmentation.py
  io/
    __init__.py
    images.py
    video.py
    export.py
    experiments.py
  application/
    __init__.py
    session.py
    processing_worker.py
    playback.py
  gui/
    __init__.py
    main_window.py
    image_view.py
    threshold_controls.py
    experiment_panel.py
    controller.py
tests/
  fixtures/color_cases.py
  unit/
  integration/
docs/
  algorithm.md
  acceptance.md
  verification.md
  demo.md
experiments/
  inputs/
  manifest.json
  environment.json
  README.md
  runs/
  report.md
  reproduction.md
  performance.md
```

**Structure Decision**: Keep the existing task paths and a single desktop package. Source,
tests and experiment artifacts above are planned outputs, not files created by this command.
The repository inventory contains README, project documentation and Spec Kit artifacts, but
no existing GUI or utility application modules to reuse. Do not introduce a dependency on
Image Restoration; reassess any later supplied reusable components against the same contracts.

Imports flow from GUI to application; application uses models, processing and I/O. Processing
and I/O may import shared models/errors, but neither imports the GUI. Experiment I/O writes a
provided snapshot; it does not run algorithms. __main__ composes the window and controller.

### Phase 0: Research Decisions

See [research.md](research.md). Resolve toolkit roles, RGB/HSV numeric behavior, hue endpoints,
thread ownership, media decoding limits, packaging order, experiment publication and validation.
No design question is deferred to an undefined implementation choice. Exact installable package
pins and measured performance are implementation evidence to collect, not unresolved architecture.

### Phase 1: Design and Contracts

- [data-model.md](data-model.md): field ranges, array representations, identity and state transitions.
- [contracts/processing.md](contracts/processing.md): pure callable contracts and numerical tests.
- [contracts/desktop-workflow.md](contracts/desktop-workflow.md): GUI actions, concurrency and failures.
- [contracts/experiment-record.md](contracts/experiment-record.md): local persistence and reproducibility.
- [quickstart.md](quickstart.md): future executable setup and end-to-end acceptance procedure.

Resolve earlier analysis findings as follows: fill constitution gates (C1); permit upper H=360
and test near-origin red (I1); prepare package metadata/dependencies before skeleton but install
the local package only after skeleton creation (I2); separate automated replay from independent
student acceptance so documentation preparation can proceed (U1). Task IDs remain stable.
Only the planning portion T001 is complete at this point; runtime tasks remain unchecked.

## Complexity Tracking

No constitution exceptions or additional infrastructure are required. One serialized worker,
revisioned snapshots and local files address the existing responsiveness/reproducibility
requirements without services, a database, or a plugin framework. Runtime verification is pending.
