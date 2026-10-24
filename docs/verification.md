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
