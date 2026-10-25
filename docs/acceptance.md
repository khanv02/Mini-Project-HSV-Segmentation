# GUI Recovery and Supported-Format Acceptance

This procedure is the reviewer-facing acceptance matrix for FR-002, FR-013, SC-001 and SC-007.
Run it from the repository root on the documented Windows demonstration computer. Automated
coverage lives in `tests/integration/test_error_recovery.py`; manual observations and any unmet
case remain visible in `docs/verification.md`.

## Required message contents

Every failure message must contain these five labeled fields. Tests compare their meaning rather
than exact prose:

1. **Operation** — the action that failed, such as opening input, decoding a frame, or saving PNG.
2. **Affected** — the input path, destination path, or HSV field.
3. **Cause** — a truthful category: missing, unreadable, unsupported, decode failure, resource
   limit, invalid parameter, write failure, or uncertain decoder termination.
4. **Preserved** — the source/frame, thresholds, result, and existing destination that remain valid.
5. **Action** — one concrete correction such as checking the path/permissions, choosing a
   supported file, reducing dimensions, correcting the displayed range/order, or retrying elsewhere.

Cancellation is normal control flow: it changes no state or file and displays no error.

## Recovery matrix

Begin with a valid image open, non-default valid thresholds, and complete mask/result. For each
case, confirm the File Input, HSV Parameters and Result Visualization sections remain labeled,
then perform the subsequent valid action without restarting the application.

| ID | Action | Expected message/state | Subsequent valid action |
| --- | --- | --- | --- |
| REC-001 | Open a nonexistent `.png` path | Missing input; previous source/threshold/result retained | Open FMT-001 |
| REC-002 | Simulate/read a permission-denied image | Unreadable input with path and permission guidance; prior state retained | Open FMT-003 |
| REC-003 | Open a corrupt file named `.png` | Decode failure; prior state retained | Open FMT-002 |
| REC-004 | Open an unsupported `.gif` | Unsupported input and supported alternatives; prior state retained | Open FMT-005 |
| REC-005 | Open a header exceeding 12,000,000 pixels or simulate allocation failure | Resource limit and smaller-input action; GUI still services events | Open FMT-004 |
| REC-006 | Open an empty/corrupt/unsupported video | Open/decode failure; current session retained | Open FMT-006 |
| REC-007 | Interrupt decoding after a valid frame | Decode failure; playback stops in error; last valid frame retained | Open a valid image |
| REC-008 | Trigger backend-ambiguous video termination | Playback stops as ended with cause still uncertain; ended-or-unreadable guidance; last frame retained | Restart video at frame 0 |
| REC-009 | Enter nonnumeric HSV text | Field plus whole-number range; old result remains labeled invalid and saving is disabled | Restore the valid integer |
| REC-010 | Enter an out-of-range HSV integer | Field plus allowed range; old result retained and saving disabled | Restore an in-range value |
| REC-011 | Set lower S/V above upper S/V | Ordering rule shown; old result retained and saving disabled | Restore ordered bounds |
| REC-012 | Cancel each open/save dialog | No error; input, thresholds, result and files unchanged | Complete a valid open/save |
| REC-013 | Decline overwrite | Existing destination bytes and session unchanged | Save to a new path |
| REC-014 | Simulate PNG permission/replacement failure | Write failure; no success; live result and old destination retained | Retry at a writable path |
| REC-015 | Close while processing/writing is pending | Window closes without waiting indefinitely or applying a late callback | Relaunch normally |

## Supported-format inventory

Generate or refresh the inventory with:

```powershell
uv run python scripts/generate_acceptance_media.py
```

The generator uses literal analytical arrays and writes `manifest.json` containing full paths,
dimensions, provenance, hashes and actual video decoder observations. The committed inventory
was generated with OpenCV 4.14.0; both videos decoded through FFMPEG with three frames.

| ID | File | Representation | SHA-256 | Recorded properties |
| --- | --- | --- | --- | --- |
| FMT-001 | `tests/fixtures/acceptance_media/rgb.png` | RGB PNG | `cae9904ec49815661a5ffdfaaa4885549e472413df6fe2eecbc43a4e7e09419b` | 4×3, RGB |
| FMT-002 | `tests/fixtures/acceptance_media/rgb.jpg` | RGB JPEG | `e10ad901d6896ed384bd13aa4b4102e9ba0686f3b1e9bd08f127f473244ccd89` | 4×3, RGB |
| FMT-003 | `tests/fixtures/acceptance_media/rgb.bmp` | RGB BMP | `7e86d1cd4d4f8fc88d4f27f3a156d6bc603ef04ca7f5878b74d5689d64cc5bbf` | 4×3, RGB |
| FMT-004 | `tests/fixtures/acceptance_media/grayscale.png` | Grayscale PNG | `818b86a5335dc036f3194750a412be330be129a54f492c3decd6795a9f066dd1` | 4×2, L normalized to RGB |
| FMT-005 | `tests/fixtures/acceptance_media/rgba.png` | RGBA PNG | `caac20dbb42db0047026bd522f6367e8050772f8e80096f59800088a9eebd341` | 4×3, stored RGB with alpha ignored |
| FMT-006 | `tests/fixtures/acceptance_media/mjpg.avi` | MJPG/AVI | `90e65d64267edb4596ce3cf6ee26f951ad0627260792455271c2115f12a40bf2` | 10×8, 3 frames, FFMPEG, MJPG |
| FMT-007 | `tests/fixtures/acceptance_media/mp4v.mp4` | mp4v/MP4 | `ef31c3451038df69d0701b4b4cf803021291e5c2e7fd0a97f0968ef6e51b8621` | 10×8, 3 frames, FFMPEG reports FMP4 |

Run the integrity/decoder check with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\integration\test_format_inventory.py -q
```

For SC-001, open all seven cases through the GUI and verify the three synchronized views. Play
at least one video through open, play, pause, threshold adjustment, end and restart. A missing
file, hash mismatch, skipped codec or unavailable required decoder is an unmet result, not a pass.
