# HSV Color Segmentation

Academic desktop application for selecting colored objects using six HSV bounds.
The implementation separates pure processing, file I/O, session coordination and GUI.

Current milestone: **Phase 8 automated work complete; independent acceptance pending**. The application
opens supported images and videos, exposes six validated HSV bounds, and presents
synchronized original, binary-mask, and segmented-result views. Video opens paused at
frame 0 and supports play, pause, end, restart and replacement. Complete current masks and
segmented results can be saved as source-resolution PNG files, including one captured video frame.
File, decode, parameter and write failures preserve the last valid session and report the failed
operation, affected item, cause category, preserved state and corrective action. It can also
record immutable experiments with notes, UUID run folders and source/artifact/environment hashes.
Ten retained inputs have two settings each; three runs replay with exact decoded pixels.

See [algorithm details](docs/algorithm.md), [demonstration script](docs/demo.md),
[stage boundaries](docs/implementation-stages.md), and [verification results](docs/verification.md).
The experiment set includes a fixed real MIT scene under directional lights 0 and 24, with
CC-BY provenance and hashes recorded. Final completion remains blocked only by the two genuine
independent-student checks; they are not represented as automated passes.

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

Normal use is offline and has no service, account, database, Image Restoration, or network
dependency. Supported still formats are 8-bit PNG/JPEG/BMP (including normalized grayscale,
alpha and palette forms). Video input is sequential local MP4/AVI decoding through OpenCV;
the published Windows fixtures use mp4v/MP4 and MJPG/AVI through FFMPEG. Codec availability
outside the recorded environment depends on the local OpenCV build.

Use the six controls as H lower/upper in degrees and S/V lower/upper in percent. Bounds are
inclusive; lower H greater than upper H wraps through zero. Save Mask and Save Result publish
source-resolution lossless PNGs. Record Experiment requires a current result plus lighting and
observation text and creates a hashed UUID run directory.

## Test

```powershell
uv run --locked --extra test pytest
```

The last full automated checkpoint has 195 passing checks. They cover shared contracts, analytical and
independent HSV references, exact threshold boundaries, extraction, supported image
normalization, session preservation, GUI structure, rapid-edit coalescing, stale-result
rejection, video decoding/lifecycle, playback state, error recovery, experiment publication,
and exact replay. Retained Phase 7 evidence uses the ten files in `experiments/manifest.json`.

Shared contracts live in `src/hsv_segmentation/models.py` and `errors.py`.
`tests/fixtures/color_cases.py` supplies 12 hand-derived colors, 11 interval
reference cases and a seeded `colorsys` sample without importing production code.

See `specs/001-hsv-color-segmentation/tasks.md` for the eight phase boundaries
and `specs/001-hsv-color-segmentation/quickstart.md` for copyable operation and replay steps.

The Full-HD GUI benchmark is reproducible with:

```powershell
.\.venv\Scripts\python.exe experiments\benchmark_performance.py
```

It retained 100/100 updates within one second on the documented machine. HSV segmentation is
not object recognition: similar colors, shadows, highlights, white balance and low saturation
can affect selection. No denoising, learned thresholds, tracking, audio or full-video encoding
is provided. See `docs/algorithm.md` for the precise limitations.

The curated `experiments/` inputs, 20 UUID runs and evidence are retained in version control;
local environments, downloaded tools, caches and build output are ignored.

To finish acceptance, a second student must genuinely replay three retained runs and a student
must independently complete the documented image/edit/compare/save flow within five minutes.
Record those results in `experiments/reproduction.md` and `docs/verification.md`; until then T049
and the dependent final review T050 remain open.
