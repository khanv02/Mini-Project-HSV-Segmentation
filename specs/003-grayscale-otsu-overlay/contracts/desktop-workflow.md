# Contract: Desktop Workflow

## Opening a source

1. The source is decoded through the existing image/video adapters.
2. The controller starts in HSV mode regardless of eligibility.
3. Exact grayscale eligibility is computed for the immutable source/frame.
4. Existing HSV controls, four previews and default-visible histogram continue to work.

## Entering and leaving Grayscale Mode

- The mode control is explicit and keyboard reachable.
- Eligible source: enter manual grayscale mode with the retained/default threshold and bright
  polarity; label intensity as the active signal and Hue as unavailable.
- Ineligible source: remain in HSV mode, retain the current result and show a concise reason.
- Leaving grayscale immediately restores normal HSV control/histogram meaning without reopening.
- Opening another source always resets the active mode to HSV.

## Manual and Otsu controls

- Manual threshold accepts only whole values `0..255`; polarity is always visible.
- Selecting Otsu schedules bounded background work and keeps the last valid result visible.
- Applied Otsu shows its resolved integer threshold and the selected polarity, and disables direct
  threshold editing until Manual is selected again.
- Unavailable/ineligible/stale Otsu shows a recoverable status and preserves the prior result.
- Switching to Manual restores the prior editable manual value without reopening the source.

## Revision and video behavior

- Source/frame, request, settings and display changes increment their corresponding identity.
- Worker completions commit only when every relevant identity matches current controller state.
- A newer frame or settings request supersedes replaceable pending work in the existing bounded
  worker; Tk callbacks never wait for processing.
- A paused eligible grayscale video frame may use Otsu. Playback/frame changes make its completion
  stale unless identity still matches.

## Histogram and previews

- HSV mode preserves current Hue, Saturation and Value histograms.
- Grayscale mode presents the intensity distribution from the common channel/Value data and
  explicitly marks Hue as not meaningful; no false Hue interpretation is shown.
- Original, Binary Mask, Result and Overlay stay synchronized to one committed result snapshot.
- Result remains selected pixels on black. Overlay remains the chosen visual evidence variant.

## Save Overlay

- The action is enabled only for a valid current `OverlaySnapshot` and when no conflicting export
  is active, following current Save Mask/Save Result behavior.
- Choosing a destination may be cancelled without changing state or creating a file.
- Before background I/O begins, the controller captures exact overlay pixels and identity.
- If UI state changes afterward, the captured snapshot is still exported truthfully; alternatively
  a pre-write identity check may explicitly reject it as stale. It may never export new pixels
  under old identity.
- Success and recoverable failure messages identify Overlay and its source/frame.

## Accessibility and compactness

- Mode, threshold source and polarity do not rely on color alone.
- Disabled/unavailable controls include a readable status reason.
- Controls remain in the compact upper control area and do not reduce the required four-preview
  workspace to a sequential pipeline.
