# Desktop Workflow Contract

User-facing application: **HSV Color Segmentation**. Planned implementation lives under
`src/hsv_segmentation/gui/`, `application/` and `io/`. No remote interface or service exists.

## Layout and Actions

- File section: Open Image, Open Video, Save Mask, Save Result, Record Experiment, status/source
  identity, and play/pause/restart with current zero-based frame index when video is active.
- Parameter section: six numeric controls. Lower H 0..359 degrees; upper H 0..360 degrees;
  both S/V bounds 0..100 percent. Clearly explain upper 360 and reversed hue intervals.
- Visualization section: simultaneously visible Original, Binary Mask and Segmented Result,
  with matching source/frame identity and aspect-preserving fitted previews. Black/white mask
  scaling uses nearest-neighbor display sampling to avoid misleading intermediate intensities.
- Experiment panel: lighting description, observations, destination and saved record location.
- Optional HSV Histogram panel: a show/hide toggle and three compact Canvas charts for the
  accepted source/frame. Charts label H/S/V axes and counts, disclose the fixed `S >= 5%` hue
  cutoff and omitted count, and overlay the last valid six bounds without choosing thresholds.

Opening is available without existing media. Threshold edits without media may change defaults
for the next open but do not create a result. Play/pause/restart apply only to loaded video.
Export/record actions require valid visible controls and a complete current displayed snapshot.
GUI callbacks validate/dispatch; they never implement HSV or file encoding algorithms.

## HSV Histogram Panel

The panel starts hidden and may be shown or hidden without changing source pixels, thresholds,
mask, result, export eligibility or experiment state. All three result views remain present.
At a 960x640 client area and 100% scaling, labels, charts, markers, toggle and six controls do
not overlap or require whole-window scrolling; each preview retains at least 160x120 pixels.

Counts are computed on the serialized worker for the exact accepted source/frame and cached by
session, frame and source hash. A threshold-only request reuses counts and updates only overlay
coordinates. A source/frame change replaces the cache. Normal revision checks reject stale
counts exactly as they reject stale segmentation results; failed opens retain prior charts.

Overlay coordinates use continuous numeric axes H 0..360 and S/V 0..100 rather than snapping
to bin rectangles. Ordered bounds shade one interval, wrapped hue shades both axis ends, and an
equal bound draws a labeled line. Shading describes the control interval, not an exact selected
pixel count. While valid edits are processing, label the overlay pending; invalid visible text
keeps and clearly labels the last-valid overlay. With no media, show an explicit no-data state.

## Open Image

The I/O adapter recognizes PNG/JPEG/BMP and normalizes supported 8-bit modes per data-model.md.
The worker fully decodes a candidate before commit; selected source files remain unchanged.
Initial thresholds select the full domain (0,360,0,100,0,100). Subsequent opens retain the last
valid set. Cancelling or failing an open preserves the previous input, controls and result.
When opening during playback, pause the old source while loading; restore its previous state
on failure/cancellation, or release it after candidate success. No stale callback may relabel
old data as the new source.

## Threshold Edits

Accept valid complete six-value sets without an Apply button. Show field-specific feedback for
out-of-range, malformed or reversed S/V bounds. Do not replace active settings with invalid text.
While edits are pending/invalid or processing is incomplete, label the previous view as pending
or invalid and disable export; do not claim it represents the unprocessed visible values.

Use a 75 ms debounce after the latest valid edit as an initial scheduling policy. One active
worker and one replaceable pending request bound work. The main thread polls results with
Tk after() and creates/updates Tk widgets/images. No worker invokes Tk methods. On valid edits,
revision numbers invalidate older jobs. A completed current result updates all views together.
The end-to-end latency measurement includes debounce and display, not just core computation.

## Open/Play/Pause/Restart Video

Require a decodable MP4/AVI file and successful first frame before committing. Convert decoded
BGR frames into RGB in I/O. Open paused at frame 0. Stream sequential frames, without whole-file
buffering, and show the same accepted frame in all views. Process then present each frame before
scheduling the next; reduced playback speed is allowed. Paused parameter edits reprocess the
retained frame. Pause stops frame advancement while keeping the frame; restart reopens the
source from its first frame and releases any previous capture.

Known fixture EOF stops cleanly and retains the last frame. Explicit retrieve/decode errors or
premature termination before a credible known frame count stop with an actionable error.
When the backend cannot distinguish exhaustion from read failure, stop with an honest
ended-or-unreadable message and offer reopen/supported encoding guidance. Do not infer a
universal diagnosis from read()==False. Frame counts are hints unless validated for the fixture.
This is a documented decoder limitation, not a reason to discard the last valid result.

## Save Mask / Save Result

Capture the entire displayed result snapshot before background writing. For video this may
briefly pause frame scheduling while capturing ownership, then resume; the captured mask,
RGB, frame index and six bounds must agree. Save full-resolution PNG L masks (0/255) or PNG
RGB extracted images. Never save the fitted preview. Reject pending/invalid/no-result export.
If destination exists, obtain overwrite confirmation. A declined overwrite or cancelled dialog
changes neither files nor session. Prefer temporary sibling output and replacement after success
to avoid corrupting an existing destination on encode failure. Success identifies the path;
failure identifies the operation and corrective action and retains the current result.

PNG encoding and experiment hashing/JSON writing execute on the serialized background worker,
never in Tk event handlers. Allow one save/record operation at a time; disable duplicate write
actions rather than accumulating snapshots. A pending accepted write is protected from replacement;
at most one separate latest compute/input request may wait behind it. Main-thread polling delivers completion/failure and
re-enables actions only when the current session permits them. The notification identifies the
captured destination/source even if input has changed. Closing the window discards UI callbacks
without an indefinite GUI-thread join. A controlled delayed writer must demonstrate that the
event loop continues servicing interaction before completion.

## Failure and Resource Rules

Every failure message identifies the operation, affected file or parameter, cause category,
preserved session state, and a concrete corrective action (FR-013). Parameter errors include
the allowed range or ordering rule. Unknown decoder causes remain explicitly uncertain.
Tests assert these contents rather than identical prose; normal cancellation requires no error.

- Missing/unreadable file: name the input operation and suggest checking path/permissions.
- Unsupported format/representation/encoding: identify the supported alternatives.
- Corrupt/empty file: explain that decoding failed; opening does not replace valid input.
- Dimensions above 12,000,000 pixels, Pillow safeguard warning/error or allocation failure:
  explain the resource limit and suggest a smaller input. Keep the old source and result.
- Unsupported/high-bit-depth image modes: report the limitation instead of silently rescaling.
- Failed save/record: identify destination and corrective action; never report success early.
- Shutdown: reject further work, stop scheduling, release capture, discard stale callbacks;
  no indefinite GUI-thread wait for background work. Handle closed-window callbacks safely.

## Observable Validation

Exercise valid image and video paths, each error/cancellation category, close during pending
work, input replacement during playback, rapid edits, and source-resolution save round trips.
Verify that a subsequent valid operation succeeds after each recoverable error. Record results
in `docs/verification.md`; this contract does not claim those checks have already run.

## Clean Workspace Presentation

- The command area keeps Open Image and Open Video visible. Save and record actions remain
  present but unavailable until a complete current result exists. Playback controls and frame
  position are absent from the empty and image contexts and appear together for video.
- The HSV inspector groups Hue, Saturation and Value vertically. Each group contains visible
  lower and upper labels, values, units and the existing synchronized slider/input behavior.
- The result workspace owns remaining width and always contains Original, Mask and Result in
  source order. Showing the histogram must not reparent or replace any preview.
- The application uses shared semantic styles for background, surface, primary action, muted
  text, borders, focus, disabled state and errors. State styling must not alter widget bounds.
- `Ctrl+O` opens the image chooser and `Ctrl+Shift+O` opens the video chooser. Keyboard focus
  follows the visible command area, inspector and visualization tools; hidden contextual controls
  cannot retain focus.
- At 960x640 and 100% scaling, with histogram shown and hidden, the whole window has no horizontal
  scrolling and each preview canvas is at least 160x120. Large windows give extra space to previews.
