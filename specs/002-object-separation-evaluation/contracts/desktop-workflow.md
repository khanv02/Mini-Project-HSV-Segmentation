# Desktop Workflow Contract

- Existing open, presets, pixel/ROI sampling, morphology, histogram, overlay, playback and save
  commands retain behavior. New analysis controls default disabled; target defaults baseline.
- Contours/boxes annotate an original-image display copy. Sampling still uses source RGB and
  existing ImageView coordinate mapping. Statistics disclose connected-region interpretation.
- Comparison selector names baseline/filtered/Watershed. Original, Mask and Result remain
  accessible simultaneously; selecting a comparison does not change Save Mask/Save Result.
- Analysis panel has labeled units/ranges, local errors, keyboard focus, collapsible/tabbed
  content and a scrollable region table. New panel must not reduce baseline minimum previews.
- Truth loader accepts PNG/BMP modes 1/L/LA/RGB/RGBA and palette resolving to grayscale;
  reject unsupported bit depths and unequal color channels. Binary 1-bit is normalized to
  0/255. Equal-channel RGB resolves to that channel; alpha ignored, never composited. Apply
  strict > threshold in 0..254; show rule before evaluation. No EXIF rotation/resizing.
- Source dimensions and current session/hash/frame must match. Loading pauses video and
  captures binding; failed/cancelled loads retain existing data and leave playback paused.
- Clearing truth increments truth revision, clears metrics and cancels pending truth commits.
  Advance, replacement and restart also clear binding; parameter edits retain it on same frame.
- Controller rejects late completions using request/settings/truth identity, including a late
  successful load after clear/replacement. Worker never opens dialogs or updates widgets.
- Pending or invalid derived settings show pending/last-valid state; extended recording is
  unavailable until every requested derived target is complete. Missing truth shows N/A.
- Insufficient markers show not-applied reason and baseline comparison; unavailable Watershed
  target is never labeled/evaluated as a successful baseline fallback.
- TP/FP/FN overlay uses distinct labeled colors and preserves masks; background TN is source.
- Failures use existing operation/affected/cause/preserved/action recovery-message structure.

## Acceptance Inventory

Automate empty/image/video control states, both connectivity choices, minimum-area validation,
Watershed statuses, truth conversion/mismatch/cancel, target selection, coverage wording,
rapid changes, delayed truth completion, video restart/advance and duplicate record prevention.
Run layout at 960x640 and large desktop, histogram shown/hidden, keyboard focus and zoom alignment.
