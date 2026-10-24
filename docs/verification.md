# Verification Record

## Phase 1: Project Setup

Scope: T001–T004 only. Later implementation phases have not started.

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
