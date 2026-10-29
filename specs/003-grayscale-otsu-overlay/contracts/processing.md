# Contract: Processing Core

## Eligibility

`classify_grayscale(rgb, source_identity) -> GrayscaleEligibility`

- Accepts only validated non-empty `uint8` RGB.
- Returns eligible exactly when `rgb[...,0] == rgb[...,1] == rgb[...,2]` for every pixel.
- Does not convert pixels, inspect filenames or use tolerance.
- Is pure and deterministic for the same pixels and identity.

## Manual intensity mask

`generate_grayscale_mask(intensity, threshold, polarity) -> BinaryMask`

- `intensity` is non-empty `uint8[H,W]`; `threshold` is an integer `0..255`.
- `bright` selects `intensity > threshold`.
- `dark` selects `intensity <= threshold`.
- Output is owned `uint8[H,W]` containing only `0` and `255`.
- At any fixed threshold the two valid polarities are exact complements.

## Otsu threshold

`compute_otsu_threshold(intensity, source_identity) -> OtsuOutcome`

- Uses a 256-bin count histogram of the complete current frame.
- Considers thresholds `0..254` for which both `I <= T` and `I > T` are non-empty.
- Maximizes between-class variance using numerically stable accumulated counts and sums.
- When several thresholds share the exact maximum, returns the smallest threshold.
- When no two non-empty classes exist, returns `unavailable` with no threshold.
- Does not apply polarity and does not mutate settings or a prior result.

## Mode-aware mask generation

`process_source(...) -> SegmentationResult`

- In `hsv`, retains current HSV conversion, histogram and mask semantics.
- In `grayscale`, validates eligibility, resolves manual/Otsu threshold, generates the original
  mask, then invokes the existing morphology, analysis, Watershed and evaluation stages.
- A requested Otsu result that is unavailable is returned as a non-committable outcome or raised
  as a typed recoverable application condition; it must not create a fabricated segmentation.
- All results carry the request's source/frame/request/settings identity.

## Overlay composition

`compose_overlay_snapshot(result, display_settings) -> OverlaySnapshot`

- Selects exactly one variant from segmentation, object analysis, Watershed or confusion.
- Uses existing pure composition primitives and source-coordinate data.
- Fails validation when a specialized variant lacks required current data; it never silently
  labels fallback pixels as the requested variant.
- Returns owned, read-only source-sized RGB pixels and complete identity metadata.
- Given equal inputs, pixels and metadata are deterministic.

## Errors and ownership

- Invalid data raises the project's typed `ValidationError` before partial output is exposed.
- Unavailable Otsu is an expected domain outcome, not a crash.
- Processing functions never import Tkinter or perform file writes.
- Input arrays are not mutated; published snapshot arrays cannot be mutated by callers.
