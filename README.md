# HSV Color Segmentation

Academic desktop application for selecting colored objects using six HSV bounds.
The implementation separates pure processing, file I/O, session coordination and GUI.

Current milestone: **Phase 4 complete — image and video segmentation**. The application
opens supported images and videos, exposes six validated HSV bounds, and presents
synchronized original, binary-mask, and segmented-result views. Video opens paused at
frame 0 and supports play, pause, end, restart and replacement. Export begins in Phase 5.

See [stage boundaries](docs/implementation-stages.md) and
[verification results](docs/verification.md). Implementation stops before Phase 5.

## Install (Windows PowerShell)

Install Windows CPython 3.11 with Tcl/Tk and `uv`, then run from this repository:

```powershell
uv sync --locked --extra test
```

`uv.lock` pins project dependencies. The first sync needs network access or cached
wheels; normal application use is offline. `requirements-lock.txt` remains as the
Phase 1 pip environment record.

To confirm the installed skeleton:

```powershell
.\.venv\Scripts\python.exe -c "import hsv_segmentation; import hsv_segmentation.processing; import hsv_segmentation.io; import hsv_segmentation.application; import hsv_segmentation.gui; print(hsv_segmentation.__version__)"
```

Launch the application with:

```powershell
uv run --locked --extra test hsv-segmentation
```

## Test

```powershell
uv run --locked --extra test pytest
```

Phases 1–4 have 154 passing checks. They cover shared contracts, analytical and
independent HSV references, exact threshold boundaries, extraction, supported image
normalization, session preservation, GUI structure, rapid-edit coalescing, stale-result
rejection, video decoding/lifecycle, and playback state. Tests create their own small
images and videos; no external dataset is needed.

Shared contracts live in `src/hsv_segmentation/models.py` and `errors.py`.
`tests/fixtures/color_cases.py` supplies 12 hand-derived colors, 11 interval
reference cases and a seeded `colorsys` sample without importing production code.

See `specs/001-hsv-color-segmentation/tasks.md` for the eight phase boundaries
and `specs/001-hsv-color-segmentation/quickstart.md` for later acceptance scenarios.

The curated `experiments/` inputs and evidence will be retained in version control;
local environments, downloaded tools, caches and build output are ignored.
