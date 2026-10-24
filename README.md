# HSV Color Segmentation

Academic desktop application for selecting colored objects using six HSV bounds.
The implementation separates pure processing, file I/O, session coordination and GUI.

Current milestone: **Phase 2 complete — shared foundation**. Package setup,
immutable media/threshold/result models, typed errors and independent reference
fixtures are available. The segmentation algorithm and desktop window will be
implemented in Phase 3; the launch command below is not available yet.

See [stage boundaries](docs/implementation-stages.md) and
[verification results](docs/verification.md). Implementation stops before Phase 3.

## Install (Windows PowerShell)

Install Windows CPython 3.11 with Tcl/Tk, then run from this repository:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -m pip check
```

For the project-local development interpreter, use `.tools\python311\python.exe`
instead of `py -3.11` when creating the virtual environment. Installation needs
network access or cached wheels; normal application use is offline.

To confirm the installed skeleton:

```powershell
.\.venv\Scripts\python.exe -c "import hsv_segmentation; import hsv_segmentation.processing; import hsv_segmentation.io; import hsv_segmentation.application; import hsv_segmentation.gui; print(hsv_segmentation.__version__)"
```

Once Phase 3 is complete, launch with:

```powershell
.\.venv\Scripts\python.exe -m hsv_segmentation
```

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Phase 2 has 60 passing foundation checks for data validation, snapshot ownership,
error context and analytical reference data. Actual algorithm tests begin in
Phase 3. The initial empty collection at Phase 1 was a setup checkpoint only.

Shared contracts live in `src/hsv_segmentation/models.py` and `errors.py`.
`tests/fixtures/color_cases.py` supplies 12 hand-derived colors, 11 interval
reference cases and a seeded `colorsys` sample without importing production code.

See `specs/001-hsv-color-segmentation/tasks.md` for the eight phase boundaries
and `specs/001-hsv-color-segmentation/quickstart.md` for later acceptance scenarios.

The curated `experiments/` inputs and evidence will be retained in version control;
local environments, downloaded tools, caches and build output are ignored.
