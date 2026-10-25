# HSV Color Segmentation

Academic desktop application for selecting colored objects using six HSV bounds.
The implementation separates pure processing, file I/O, session coordination and GUI.

Current milestone: **Phase 7 complete — reproducible experiment recording and comparison**. The application
opens supported images and videos, exposes six validated HSV bounds, and presents
synchronized original, binary-mask, and segmented-result views. Video opens paused at
frame 0 and supports play, pause, end, restart and replacement. Complete current masks and
segmented results can be saved as source-resolution PNG files, including one captured video frame.
File, decode, parameter and write failures preserve the last valid session and report the failed
operation, affected item, cause category, preserved state and corrective action. It can also
record immutable experiments with notes, UUID run folders and source/artifact/environment hashes.
Ten retained inputs have two settings each; three runs replay with exact decoded pixels.

See [stage boundaries](docs/implementation-stages.md) and
[verification results](docs/verification.md). Phase 8 has not started. Phase 7 includes a fixed
real MIT scene under directional lights 0 and 24, with CC-BY provenance and hashes recorded.

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

The project has 195 passing checks. They cover shared contracts, analytical and
independent HSV references, exact threshold boundaries, extraction, supported image
normalization, session preservation, GUI structure, rapid-edit coalescing, stale-result
rejection, video decoding/lifecycle, playback state, error recovery, experiment publication,
and exact replay. Retained Phase 7 evidence uses the ten files in `experiments/manifest.json`.

Shared contracts live in `src/hsv_segmentation/models.py` and `errors.py`.
`tests/fixtures/color_cases.py` supplies 12 hand-derived colors, 11 interval
reference cases and a seeded `colorsys` sample without importing production code.

See `specs/001-hsv-color-segmentation/tasks.md` for the eight phase boundaries
and `specs/001-hsv-color-segmentation/quickstart.md` for later acceptance scenarios.

The curated `experiments/` inputs, 20 UUID runs and evidence are retained in version control;
local environments, downloaded tools, caches and build output are ignored.
