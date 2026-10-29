# Data Model: Grayscale, Otsu and Overlay Export

## Shared conventions

- All image arrays are non-empty NumPy arrays owned by immutable snapshots.
- RGB and overlay pixels are `uint8[height, width, 3]`.
- Binary masks are `uint8[height, width]` containing only `0` and `255`.
- Intensity and threshold values use the inclusive integer domain `0..255`.
- A snapshot identity is the tuple of session, source hash, optional frame index, request revision
  and settings revision. Ground-truth identity is also required for a confusion overlay.
- Model defaults describe the existing HSV workflow so old construction sites remain meaningful.

## SegmentationMode

A closed value set carried by requests, results and experiment evidence.

| Value | Meaning |
|---|---|
| `hsv` | Existing Hue/Saturation/Value range segmentation; default. |
| `grayscale` | Explicit intensity thresholding for an exactly eligible source/frame. |

Validation: no other value is accepted. Opening any new source creates `hsv`, never `grayscale`.

## GrayscaleSettings

Immutable user intent for grayscale segmentation.

| Field | Type | Validation | Meaning |
|---|---|---|---|
| `threshold_source` | `manual | otsu` | closed set | Whether the applied threshold is entered or computed. |
| `manual_threshold` | integer | `0..255`, not bool | Editable value preserved even while Otsu is selected. |
| `polarity` | `bright | dark` | closed set | Foreground side of the threshold. |
| `settings_revision` | integer | `>= 0` | Monotonic identity for async commit checks. |

The resolved Otsu threshold is not stored as mutable user intent. It belongs to `OtsuOutcome` in
the result for a particular source snapshot.

## GrayscaleEligibility

Immutable source-derived fact.

| Field | Type | Meaning |
|---|---|---|
| `eligible` | boolean | True only when every RGB triplet has equal channels. |
| `reason` | optional text | Stable user-facing explanation when false. |
| `source_sha256` | 64-character hex | Pixel-source identity checked before reuse. |
| `frame_index` | optional integer | Video frame identity. |

Validation: an eligible outcome has no failure reason; an ineligible outcome has a non-empty
reason. It is never inferred from filename or file metadata.

## OtsuOutcome

Immutable result of asking for a global Otsu threshold.

| Field | Type | Validation | Meaning |
|---|---|---|---|
| `status` | `applied | unavailable | not_requested` | closed set | Honest result state. |
| `threshold` | optional integer | required only for `applied`, `0..254` | Smallest optimal split. |
| `reason` | optional text | required for `unavailable` | Why no threshold was fabricated. |
| `tie_rule` | text | fixed `smallest_optimal_threshold` | Reproduction rule. |
| `source_sha256` | hex text | matches source | Source identity. |
| `frame_index` | optional integer | matches frame | Frame identity. |

An unavailable outcome never replaces the last committed `SegmentationResult`.

## ProcessingRequest additions

Existing fields remain. Add:

| Field | Type | Default | Cross-field validation |
|---|---|---|---|
| `segmentation_mode` | `SegmentationMode` | `hsv` | `grayscale` requires current eligibility. |
| `grayscale_settings` | `GrayscaleSettings` | default manual/128/bright/revision 0 | Used only when mode is grayscale. |

The request remains an immutable source snapshot. Rejected mode changes do not create a request
or invalidate the last committed HSV result.

## SegmentationResult additions

Existing mask/result/downstream fields remain. Add:

| Field | Type | Meaning |
|---|---|---|
| `segmentation_mode` | `SegmentationMode` | Algorithm that produced `original_mask`. |
| `grayscale_settings` | `GrayscaleSettings` | Intent snapshot associated with this result. |
| `grayscale_eligibility` | `GrayscaleEligibility` | Source-derived eligibility evidence. |
| `otsu_outcome` | `OtsuOutcome` | Resolved threshold provenance or not-requested state. |

Cross-field invariants:

- `hsv` results retain existing threshold and histogram meaning and have no applied Otsu outcome.
- `grayscale` results must be eligible and apply the resolved manual or Otsu threshold exactly.
- `mask` remains the post-morphology binary mask; `original_mask` is the direct selection mask.
- `segmented_rgb` keeps source RGB for selected pixels and black elsewhere in either mode.
- Analysis, Watershed and evaluation dimensions match the source as before.

## OverlayVariant

Closed value set describing the exact Overlay preview.

| Value | Required data |
|---|---|
| `segmentation` | source and current binary mask |
| `object_analysis` | source and current component analysis |
| `watershed` | source and current applied/empty Watershed result |
| `confusion` | source, current prediction and matching ground truth |

Fallback is explicit: if a requested specialized variant is unavailable, the UI selects and
labels `segmentation` before a snapshot is created. The snapshot never claims one variant while
containing another.

## OverlayDisplaySettings

Immutable presentation inputs needed to reproduce exact pixels: selected variant, segmentation
tint RGB/opacity, contour/box visibility and any fixed palette version. It carries a display
revision incremented whenever these choices change.

## OverlaySnapshot

Immutable export hand-off.

| Field | Type | Meaning |
|---|---|---|
| `rgb` | immutable RGB array | Exact source-sized Overlay pixels. |
| `variant` | `OverlayVariant` | Honest composition identity. |
| `display_settings` | `OverlayDisplaySettings` | Pixel-affecting presentation choices. |
| `source_path`, `source_sha256` | path/text | Source identity. |
| `session_id`, `frame_index` | text/optional integer | Session/frame identity. |
| `request_revision`, `settings_revision`, `display_revision` | integers | Async identity. |
| `truth_pixel_sha256` | optional hex text | Required for confusion variant. |

Validation: array dimensions match the source; confusion requires truth identity; all arrays are
copied and marked read-only. Export operates on this object, not live GUI state.

## Experiment schema 3 evidence

Schema 3 retains all applicable schema 2 fields and adds:

- `segmentation.mode` (`hsv` or `grayscale`)
- for grayscale: `threshold_source`, `threshold`, `manual_threshold`, `polarity`, `tie_rule`,
  eligibility and settings revision
- optional `overlay.variant`, display settings, artifact path, PNG file SHA-256 and decoded-pixel
  SHA-256

Schema selection:

- Existing plain HSV record: schema 1.
- Existing HSV record with analysis/Watershed/evaluation: schema 2.
- Any grayscale record or record retaining overlay evidence: schema 3.

## State transitions

```text
Open source/frame
  -> HSV active, eligibility computed, prior Otsu outcome cleared

HSV active + request grayscale
  -> eligible: grayscale manual active, bright polarity default
  -> ineligible: remain HSV, explain rejection, preserve result

Grayscale manual + edit threshold/polarity
  -> increment settings/request revision -> worker -> exact-current result commits

Grayscale + request Otsu
  -> pending while last result stays visible
  -> applied: Otsu result commits and labels computed threshold
  -> unavailable/stale: preserve last valid result and report status

Any valid result + change overlay display
  -> increment display revision -> compose and show new OverlaySnapshot

Save Overlay
  -> capture current immutable OverlaySnapshot -> background atomic PNG write
  -> later UI changes do not mutate captured pixels or identity
```
