# Verification Record

## Phase 1: Project Setup

Scope of this historical setup checkpoint: T001–T004 only.

The Windows CPython installer was downloaded from python.org and its valid
Python Software Foundation Authenticode signature was checked before installation.
The project-local interpreter is Python 3.11.9 x64, with Tcl 8.6.12 and Tk 8.6.
The MSYS Python on PATH is not used for this project's Windows environment.

Completion checks (all performed successfully):

1. Install the chosen runtime/test/build dependencies into a fresh `.venv`.
2. Save exact installed direct/transitive/build versions in `requirements-lock.txt`.
3. Install the local package from `src/` with no dependency resolution/build isolation.
4. Import the root, processing, I/O, application and GUI packages independently.
5. Run `python -m pip check` and `python -m pytest --collect-only`.
6. Confirm Git ignores environments, downloaded tools, bytecode and build output.

An empty pytest collection returns code 5 and is expected at this phase. A test
import/configuration error is not accepted. No dummy tests are added to disguise
the absence of the later algorithm suite. GUI launch and functional tests belong
to later phases and are not claimed here.

### Recorded results — 2026-10-24

| Check | Result |
| --- | --- |
| Fresh virtual environment | Created from project-local Windows CPython 3.11.9 x64 |
| Runtime dependencies | NumPy 2.4.6, Pillow 12.3.0, OpenCV 4.14.0.94 imported successfully |
| Test/build tools | pytest 9.1.1, setuptools 84.2.1, wheel 0.48.0, pip 26.2.2 |
| Tcl/Tk | Tcl 8.6.12; tkinter reports Tk 8.6 |
| Dependency lock | `pip freeze --all` recorded all direct/transitive/build versions before local package installation |
| Editable package installation | `pip install --no-index --no-deps --no-build-isolation -e .` succeeded |
| Independent imports | Root, processing, I/O, application and GUI namespaces all imported |
| Installed source location | `src/hsv_segmentation/__init__.py` |
| Dependency consistency | `pip check`: No broken requirements found |
| Test discovery | `pytest --collect-only`: root/config/testpaths correct; 0 items; expected exit 5 |
| Ignore rules | `.tools/`, `.venv/`, bytecode and build output confirmed by `git check-ignore` |

`requirements-lock.txt` is the complete version list; no local editable path is
embedded in it. Runtime/application algorithms and GUI behavior are not tested
or implemented by these setup checks. Phase 1 (T001–T004) is complete; stop before T005.

## Phase 2: Shared Foundation

Scope: T005-T007 only. No RGB-to-HSV conversion, thresholding algorithm, file adapter,
session coordinator or GUI implementation has been added in this phase.

### Implemented contracts

- `models.py`: InputMedia, HSVThresholdSet, ProcessingRequest, SegmentationResult and
  the shared validate_rgb contract, without GUI, codecs, or filesystem access.
- Integer/interval validation rejects bools, fractional/nonfinite values, invalid revisions
  and reversed S/V bounds. Reversed hue and upper endpoint 360 are retained.
- Media validates absolute-path/hash representation, source format, image/video frame and
  backend rules. Dimensions derive from RGB, with an inclusive 12,000,000-pixel cap.
  No source path is opened and no file hash is computed by the model.
- Immutable source/result snapshots use bytes-backed array copies. Caller mutations, writes
  to a snapshot and attempts to re-enable its write flag cannot alter accepted pixels.
- Result identity derives from composed source and threshold snapshots; mask representation
  and extracted-pixel consistency are checked. Correct HSV membership remains Phase 3 work.
- `errors.py`: typed validation, input, decode and write failures carrying field or file-operation
  context, without GUI calls or file access.
- `tests/fixtures/color_cases.py`: 12 analytical colors, 11 literal interval/mask cases with
  adjacent nextafter values, exact red-extraction data, and a seed-20261024 16x16 colorsys sample.
  The factories import no production code and return fresh arrays.

### Recorded checks - 2026-10-24

Tests were written before implementation. Initial runs failed collection because the required
models/errors and fixture modules did not yet exist. After implementation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_models.py tests/unit/test_errors.py tests/unit/test_reference_cases.py -q
```

Result: **60 passed in 1.87 seconds**, under the Phase 1 Windows CPython 3.11.9 environment.
Checks cover normal/boundary/invalid data, exact frame/parameter identity, inclusive size limits,
independent snapshot ownership, invalid result rejection, contextual errors, deterministic
sampling and analytical reference values. Separate subprocess checks confirm shared models do
not load GUI/file adapters and fixtures do not load production modules.

Conversion-reference tolerances are circular hue error <=1e-10 degrees and S/V absolute error
<=1e-10 percentage points, relative tolerance zero. These check independent reference data;
they do not establish correctness of an unimplemented production conversion algorithm.

T005-T007 are complete. Stop before T008; GUI and algorithm acceptance remain unexecuted.

## Phase 3: Still-Image MVP

Scope: T008-T021 only. Video, saving/export, the 10-image experiment collection and
final performance/human acceptance remain later phases.

### Processing implementation and tests

Tests were added before the corresponding modules. The first processing run failed
collection with `ModuleNotFoundError` for `processing.color` and
`processing.segmentation`, demonstrating that the tests exercised missing behavior.
The completed pure processing layer now provides:

- vectorized NumPy float64 RGB-to-HSV conversion using guarded max/min/delta equations;
- exact validation of the six integer bounds without rounding, clamping or swapping;
- inclusive ordered and wrapped-hue mask generation with uint8 values 0/255; and
- extraction that retains selected source RGB exactly and blacks excluded pixels.

The 58 new processing checks cover 12 analytical colors, a deterministic 16x16
`colorsys` oracle, continuous hue near 360 degrees, exact/nextafter boundaries,
equal and wrapped intervals, full/no selection, invalid arrays and bounds, channel
order, size limits, output ownership and source immutability. Processing imports no
GUI or file adapter.

### Still-image application

The Pillow adapter fully decodes PNG/JPEG/BMP candidates before session commit,
normalizes supported 8-bit L/LA/RGB/RGBA/P modes to RGB, replicates grayscale,
ignores alpha without compositing, hashes source bytes and enforces the 12,000,000
pixel policy. Failed and cancelled candidates preserve the previous session.

The Tk application is available through `python -m hsv_segmentation`. It separates
File Input, HSV Parameters and Result Visualization, with labeled Original, Binary
Mask and Segmented Result views. Preview fitting preserves aspect ratio and never
resizes processing data. Six spinbox/text controls show units and ranges, explain
hue wrapping, debounce valid changes by 75 ms and keep invalid text out of active
settings.

A single-worker coordinator retains one active and one replaceable pending request.
Plain completions are polled on the Tk thread; source, parameter and request revisions
discard stale work. The integration walkthrough created its own temporary color PNG,
opened it asynchronously, issued three rapid threshold revisions and verified that
the session and both output views matched only the final thresholds. It also verified
clean controller shutdown and unchanged source-file bytes. No external image dataset
is required for this phase.

### Recorded checks - 2026-10-24

Initial red checks:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_color_conversion.py tests/unit/test_segmentation.py -q
.\.venv\Scripts\python.exe -m pytest tests/integration/test_image_input.py -q
.\.venv\Scripts\python.exe -m pytest tests/integration/test_image_session.py -q
```

The processing and integration tests initially failed because their target modules
did not exist. After implementation, the final project checkpoint was:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q src tests
```

Result: **137 passed in 2.71 seconds**; dependency check reported no broken
requirements; all source and test modules compiled successfully. Of the 137 checks,
60 are the Phase 2 foundation suite, 58 cover the processing contract, and 19 cover
image input/session/GUI integration.

A live launch exposed a Windows Tk window titled `HSV Color Segmentation` to the
accessibility API. Automated visual control was stopped when concurrent user input
was detected, as required by the UI automation safety policy; no personal image was
opened. The deterministic hidden-Tk integration walkthrough remains the recorded
functional GUI evidence for this phase.

T008-T021 are complete. Stop before T022; no video implementation has started.

## Phase 4: Sequential Video Segmentation

Scope: T022-T027 only. This phase adds local MP4/AVI frame viewing and segmentation;
it does not add audio, seeking, tracking, full-video encoding or frame export.

### Decoder and lifecycle

Tests were written before implementation and initially failed collection because
`io.video` and `application.playback` did not exist. The completed OpenCV adapter:

- requires a readable `.mp4` or `.avi` file and a successfully decoded first frame
  before the application replaces its current source;
- decodes sequentially with `grab`/`retrieve`, converts BGR to RGB at the I/O boundary,
  applies the 12,000,000-pixel frame limit and retains one current frame rather than
  buffering the video;
- carries one session identity across frame indices and reopens the capture for restart;
- releases captures after failure, replacement, restart and shutdown; and
- distinguishes explicit retrieve/decode failure from known-fixture EOF. Ordinary
  backend frame counts remain hints: an unprovable failed acquisition reports
  `Video ended or the next frame could not be read; reopen or try a supported encoding.`
  rather than claiming clean EOF.

Reproducible real fixtures are generated in temporary directories. The AVI fixture uses
MJPG and the MP4 fixture uses `mp4v`; both contained three 10x8 RGB color frames. On the
recorded Windows environment, OpenCV 4.14.0 decoded the MJPG/AVI fixture through the
FFMPEG backend and reported all three frames. Exact lifecycle doubles separately cover
empty input, failed open, retrieve failure, premature trusted-fixture termination,
ambiguous untrusted termination, restart and idempotent cleanup.

### Playback and GUI acceptance

`PlaybackSession` exposes explicit empty, paused, playing, ended, error and closed states.
Video opens paused at zero; the Tk controller submits first-frame/open, next-frame and
restart work through the same serialized worker used by images. A frame is processed and
accepted before another is scheduled, so all three views and the visible frame index refer
to one immutable snapshot even when playback is slower than the file rate. Paused threshold
edits reprocess the retained frame. Replacing a video releases the old reader, and obsolete
frame completions cannot overwrite the new session.

The deterministic GUI walkthrough generated a 12-frame MJPG/AVI, opened at frame 0,
played to frame 2 or later, paused without further advancement, reprocessed that paused
frame with a new threshold revision, continued to the end, restarted at frame 0, and
replaced it with a second generated video. Original/mask/result arrays were compared to
the committed result after replacement. Controller shutdown and late-resource cleanup are
also automated. No external video or image dataset is required.

### Recorded checks - 2026-10-24

```powershell
.\.venv\Scripts\python.exe -m pytest tests/integration/test_video_input.py tests/integration/test_playback.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q src tests
```

Final result: **154 passed in 3.95 seconds**, with no skipped tests. Dependency
consistency and bytecode compilation also passed. Phase 4 contributes 17 checks for
real/fake video input, playback/session transitions, end/restart/replacement, GUI frame
synchronization and cleanup.

T022-T027 are complete. Stop before T028; PNG export has not started.

## Phase 5: Lossless PNG Output

Scope: T028-T032 only. This phase adds source-resolution mask and segmented-result
PNG export for still images and individual displayed video frames. Experiment records,
the comprehensive recovery matrix and the 10-image evaluation remain later phases.

### Output adapter and atomic writes

Tests were added before implementation. The initial focused run failed collection with
`ModuleNotFoundError: hsv_segmentation.io.export`, confirming that the new checks exercised
missing behavior. The completed adapter now:

- writes masks as PNG L with exact uint8 values 0/255 and results as PNG RGB;
- preserves source dimensions and decoded pixel values exactly;
- validates array shape, dtype, mask values and `.png` destinations;
- refuses unconfirmed overwrite and uses a temporary sibling plus `os.replace` so a failed
  encoding/replacement does not corrupt an existing destination; and
- raises contextual `WriteError` failures with destination, operation and retry guidance.

### Snapshot and GUI coordination

The File Input section now provides Save Mask and Save Result actions. They are enabled only
for a complete result matching the current valid controls. Cancellation and declined overwrite
leave files and session state unchanged. Each accepted export captures the immutable result
before dispatch, then performs PNG encoding on the existing single-thread worker. Only one
write is accepted at a time; duplicate actions are disabled while it is pending. A protected
pending write cannot be replaced by later input/processing work; that work still coalesces to
one latest request and runs after the accepted export.

A controlled delayed writer verified that Tk continued servicing scheduled interaction while
the write was blocked, work ran off the GUI thread, a replacement input could be requested,
and completion retained the captured source identity rather than relabeling it as the new source.
Closing during a delayed write discarded late UI completion safely. Simulated write failure
preserved the current result and re-enabled a retry after the error was reported.

The real-video export check generated a local 12-frame MJPG/AVI, played beyond frame zero,
captured one displayed immutable frame while playback was active, saved its segmented RGB
pixels exactly, verified the receipt's session/frame identity, and confirmed playback resumed
or reached its normal end. No fitted preview data enters an export.

### Recorded checks - 2026-10-24

```powershell
.\.venv\Scripts\python.exe -m pytest tests/integration/test_image_export.py tests/integration/test_export_session.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q src tests
```

Focused result: **18 passed in 2.88 seconds**. Final project result: **172 passed in
7.76 seconds**, with no skipped tests. Dependency consistency reported no broken
requirements, and all source/test modules compiled successfully.

T028-T032 are complete. Stop before T033; comprehensive Phase 6 recovery work has not started.

## Phase 6: Comprehensive Error Recovery

Scope: T033-T036 only. This phase makes recovery behavior explicit and testable for invalid
files, parameter mistakes, decoder interruption, resource limits, cancelled dialogs and failed
writes. Experiment persistence and the 10-image evaluation remain Phase 7 work.

### Structured recovery behavior

User-visible failures now contain five labeled fields: operation, affected file/parameter,
truthful cause category, preserved state and a concrete corrective action. Candidate image/video
opens remain atomic: missing, unreadable, corrupt, unsupported and oversized inputs never replace
the prior valid session. Explicit video decode failure stops playback in the error state and keeps
the last valid frame; backend-ambiguous termination stops safely as ended while stating that the
cause is uncertain and offering reopen/encoding guidance. Restart remains available.

Invalid HSV text now states the field's numeric range, out-of-range integers retain the displayed
range, and reversed S/V bounds state the ordering rule. Invalid visible controls preserve the old
result but disable export until corrected; correcting the fields reprocesses the current source.
Open/save cancellation and overwrite decline remain silent state-preserving control flow.

The oversized-input test deliberately blocked the loader on the background worker and confirmed
that Tk serviced another scheduled event before the resource-limit failure completed. A very fast
fake video failure also exposed a worker callback deadlock: `Future.add_done_callback` may invoke
immediately when work already finished. The worker now uses a reentrant state lock, preserving its
bounded ordering while allowing that synchronous completion path.

### Published format set

`tests/fixtures/generate_acceptance_media.py` generated and hashed FMT-001 through FMT-007 under
`tests/fixtures/acceptance_media/`. The inventory contains RGB PNG/JPEG/BMP, grayscale PNG, RGBA
PNG, MJPG/AVI and mp4v/MP4. On this OpenCV 4.14.0 environment both three-frame videos decoded
through FFMPEG; the reported FOURCC values were MJPG and FMP4. The committed manifest's seven
hashes were rechecked before decoder smoke tests. Full paths, hashes, dimensions and the reviewer
procedure are recorded in `docs/acceptance.md`.

### Recorded checks - 2026-10-24

```powershell
.\.venv\Scripts\python.exe -m pytest tests/integration/test_error_recovery.py tests/integration/test_format_inventory.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q src tests
```

Focused result: **13 passed in 3.38 seconds**. Final project result: **185 passed in
9.10 seconds**, with no skipped tests. Dependency consistency reported no broken requirements,
and all source/test modules compiled successfully.

T033-T036 are complete. Stop before T037; experiment recording and collection work has not started.

## Phase 7: Experiment Records and Comparisons

Scope: T037-T044. The implementation publishes one UUID-named directory per immutable snapshot.
`mask.png` and `result.png` are written before an atomically replaced `record.json`; failed
artifact writes never publish a complete record. Records include UTC time, source/frame identity,
six integer thresholds, lighting/observation text, relative paths, and SHA-256 values for source,
environment, PNG bytes and decoded pixels.

The GUI adds an Experiment Record panel and serializes hashing/PNG/JSON work through the existing
background worker. Tests confirm responsive event handling, disabled duplicate writes, captured
identity across source replacement, and safe close during delayed publication.

`experiments/manifest.json` indexes 10 distinct images and two threshold settings each.
`experiments/runs/` contains 20 complete records, masks and results. The report links both
comparisons for every input and avoids accuracy claims without ground truth. Three runs are
automatically reconstructed after source/environment hash checks and compared by exact decoded
mask/result pixels. The independent-student form remains honestly pending.

The manifest documents permitted reuse and attribution for all inputs. Its MIT CSAIL pair shows
the same photographed scene under directional lights 0 and 24, satisfying the real-lighting
condition. No synthetic or unrelated pair is presented as real evidence. T037-T044 are complete.

### Recorded checks - 2026-10-24

```powershell
.\.venv\Scripts\python.exe experiments\generate_evidence.py
.\.venv\Scripts\python.exe -m pytest tests\integration\test_experiment_records.py tests\integration\test_experiment_reproduction.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q src tests experiments\generate_evidence.py
```

Evidence generation published **20 runs for 10 distinct images**. Focused result: **10 passed in
1.52 seconds**. Final project result: **195 passed in 9.12 seconds**, with no skipped tests.
Dependency consistency reported no broken requirements, and all source/test/generator modules
compiled successfully. Task ledger: **44/50 complete** at the Phase 7 checkpoint.

## Phase 8: Polish and acceptance status

T045-T048 are complete. `docs/algorithm.md` records the implemented equations and limits;
`experiments/performance.md` retains a real 100-edit Full-HD Tk measurement; README, quickstart,
and `docs/demo.md` provide the operational and presentation instructions.

The first performance run failed with 13/100 updates within one second (median 1,399.77 ms).
After caching HSV per immutable `(session_id, frame_index)` and avoiding redundant Original-view
rendering, the accepted run achieved **100/100**, median **557.28 ms**, p95 **638.01 ms**, and
maximum **903.43 ms**. Every measured final output was also compared exactly with fresh pure
processing. Individual samples are in `experiments/performance_results.json`.

Automated checkpoint on 2026-10-25:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q src tests experiments\benchmark_performance.py experiments\generate_evidence.py
```

Result: **195 passed in 8.97 seconds**, no broken requirements, and successful compilation.
The runtime source contains no network client and has no Image Restoration dependency.

### FR/SC evidence matrix

`PASS` means the stated automated or retained-artifact evidence was executed on the recorded
machine. `PENDING` is deliberately not a pass.

| ID | Tasks | Test/procedure and actual outcome | Evidence | Status |
|---|---|---|---|---|
| FR-001 | T015,T020,T034 | Tk checks found the named window and labeled input, parameter, experiment and three-view sections. | `test_image_session.py`; `main_window.py` | PASS |
| FR-002 | T014,T016,T022,T024,T027,T034,T047,T049 | All FMT-001..007 fixtures opened; MJPG/AVI and mp4v/MP4 decoded through FFMPEG. | `test_format_inventory.py`; `docs/acceptance.md` | PASS |
| FR-003 | T017,T020,T025,T026 | Image and first paused video frame produced matching original/mask/result snapshots. | image/playback integration tests | PASS |
| FR-004 | T008-T012,T045 | Analytical and `colorsys` comparisons passed; equations match float64 implementation. | unit processing tests; algorithm doc | PASS |
| FR-005 | T011,T018,T045 | Six integer controls, displayed units/ranges and validation cases passed. | segmentation/image-session tests | PASS |
| FR-006 | T009,T011,T012 | Inclusive endpoints, equal intervals and wrapped hue cases passed exactly. | `test_segmentation.py` | PASS |
| FR-007 | T009,T012,T021,T028,T030 | Masks were only 0/255; retained RGB and black exclusions matched source dimensions exactly. | segmentation/export tests | PASS |
| FR-008 | T018-T021,T033,T035 | Automatic update, invalid-edit preservation, coalescing and stale-result rejection passed. | image-session/error-recovery tests | PASS |
| FR-009 | T015,T020,T021,T026 | Three synchronized source-aspect previews matched the committed source/frame. | image-session/playback tests | PASS |
| FR-010 | T022-T027 | Open-paused, play, pause, edit, EOF, restart and replacement checks passed. | video/playback tests | PASS |
| FR-011 | T028-T032 | Still and displayed-video-frame PNGs reopened at exact dimensions/pixels. | image-export/export-session tests | PASS |
| FR-012 | T029-T032,T037,T040 | Overwrite/cancel/failure, captured snapshot, background write and responsive Tk checks passed. | export/experiment-record tests | PASS |
| FR-013 | T006,T024,T030,T033-T036 | Invalid file/parameter/decode/write/resource cases had required recovery fields and allowed a valid follow-up. | error-recovery and format tests | PASS |
| FR-014 | T005,T037,T039,T040 | UUID records retained identity, frame, thresholds, UTC date, descriptions, paths and hashes. | experiment-record tests; retained runs | PASS |
| FR-015 | T038,T041-T044,T049 | Ten licensed inputs, two settings each, real-light pair, environment/procedure and exact automated replay are retained. | manifest, report, reproduction test | PASS |
| FR-016 | T002-T004,T047,T049,T050 | Full suite/workflows ran locally; source/dependencies contain no service or Image Restoration integration. | `pyproject.toml`; import review; full suite | PASS |
| FR-017 | T007-T013,T045,T050 | Pure core tests cover conversion, inclusive/wrapped selection, extraction, boundaries and invalid data without Tk/files. | unit suite; algorithm doc | PASS |
| SC-001 | T014,T016,T022,T024,T027,T034,T049 | All seven hashed format cases passed; video lifecycle completed without mismatched views. | format/playback tests; inventory | PASS |
| SC-002 | T007-T013 | All analytical/reference pixels and extracted colors matched exactly within documented tolerance. | unit processing suite | PASS |
| SC-003 | T019,T021,T046 | Full-HD real-GUI measurement achieved 100/100 <=1 s; final pixels matched final controls. | performance markdown/JSON | PASS |
| SC-004 | T028-T032 | Every automated image and video-frame export reopened with exact dimensions/pixels. | export integration tests | PASS |
| SC-005 | T037-T043,T049 | Twenty runs/ten images/light pair and three automated exact replays pass; second-student replay has not occurred. | runs, manifest, reproduction record | **PENDING** |
| SC-006 | T047-T049 | Five-minute no-help student workflow is prepared but no genuine participant/time is recorded. | quickstart, demo, reproduction form | **PENDING** |
| SC-007 | T033-T036,T049 | Automated invalid-file/parameter/save cases verified message fields, preservation and valid follow-up. | error-recovery tests | PASS |
| SC-008 | T038,T042,T044,T048,T049 | Report labels two comparisons for all ten images and discusses misses, unwanted selection and lighting. | experiment report; demo | PASS |

T049 remains incomplete because SC-005's second-student replay and SC-006's independent timed
workflow require real participants. T050 remains dependency-blocked by T049. No checkbox is
advanced for either task. Current ledger: **48/50 complete**.
