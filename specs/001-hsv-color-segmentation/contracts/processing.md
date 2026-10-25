# Processing Interface Contract

This public in-process interface supports independent tests, the desktop coordinator and
experiment replay. Planned module paths match `tasks.md`; signatures below describe behavior,
not implementation code.

## Common Representations

See [data model](../data-model.md). Input RGB is nonempty uint8 (height,width,3), within the
project pixel limit. All returned arrays are new owned arrays; caller inputs are unchanged.
Core functions neither import GUI modules nor access files, dialogs or mutable global settings.
Invalid type, shape, bounds or nonfinite HSV data raises a typed ValidationError with its field.

## rgb_to_hsv(rgb) -> hsv

Module: `src/hsv_segmentation/processing/color.py`.

Return float64 HSV in degrees and percent. Cast RGB to float64 before subtraction/division.
For RGB normalized by 255, let M=max(r,g,b), m=min(r,g,b), delta=M-m:

- V = 100*M.
- S = 0 if M=0, otherwise 100*delta/M.
- H = 0 if delta=0.
- Otherwise H = 60*((g-b)/delta mod 6) when M=r;
  H = 60*((b-r)/delta + 2) when M=g;
  H = 60*((r-g)/delta + 4) when M=b.
- Canonicalize H modulo 360. Evaluate branch divisions only where delta is nonzero;
  use red, then green, then blue precedence for tied maxima.

No epsilon is added to denominators. No hue/saturation/value is rounded to control steps.
Neutral pixels use H=0 even though hue is physically undefined there. Unit tests compare circular
hue error <=1e-10 degrees and S/V absolute error <=1e-10 percentage points, relative tolerance 0,
against hand-derived cases and scaled stdlib colorsys. Tolerance is for conversion tests only.

## validate_thresholds(thresholds) -> validated thresholds

Module: `src/hsv_segmentation/processing/thresholds.py`.

Accept exactly six named integer values, rejecting bool/fractional/nonfinite/missing values.
Lower H range is 0..359; upper H is 0..360. S/V range is 0..100 with lower<=upper for each.
Reversed hue is valid. Return the validated immutable set or raise ValidationError;
never silently clamp values, reorder intervals or change upper 360 to zero.

## generate_mask(hsv, thresholds) -> mask

Module: `src/hsv_segmentation/processing/segmentation.py`.

Validate float64 HSV and bounds. Ordered hue selects lower_h_deg <= H <= upper_h_deg;
wrapped hue selects H >= lower_h_deg OR H <= upper_h_deg. Intersect this with inclusive ordered
S and V selections. Return uint8 (height,width) with selected=255 and unselected=0.
No floating tolerance widens interval membership. Equal bounds below 360 select that value only.
The interval [0,360] selects every canonical hue; [0,359] does not.

## apply_mask(rgb, mask) -> segmented_rgb

Module: `src/hsv_segmentation/processing/segmentation.py`.

Require matching height/width, RGB uint8 and mask uint8 with values only 0/255. Return new
uint8 RGB preserving selected colors exactly and using (0,0,0) elsewhere. Never reconstruct
selected RGB from HSV, which could alter pixel values.

## segment(rgb, thresholds) -> (mask, segmented_rgb)

Module: `src/hsv_segmentation/processing/segmentation.py`.

Compose the authoritative conversion, selection and extraction functions. Application code may
reuse a validated cached HSV image when only thresholds change, without duplicating algorithms.
Pure functions do not attach GUI state; the application adds source and revision metadata.

## compute_hsv_histogram(hsv) -> HSVHistogram

Module: `src/hsv_segmentation/processing/histogram.py`.

Validate the same float64 HSV contract used by mask generation without mutating the input.
Return 360 hue counts and 101 counts each for saturation and value. Bin assignment uses the
integer part (`floor`) of each nonnegative component; exact S/V 100 remains in bin 100. Hue is
counted only for pixels whose unrounded saturation is `>= 5.0`; pixels below that fixed display
cutoff increment `excluded_hue_count`. Saturation and value always include every pixel.

The histogram is descriptive and independent of all six thresholds. For `N` pixels,
`sum(H) + excluded_hue_count = sum(S) = sum(V) = N`. Empty included-hue data is valid for a
fully neutral image. The result arrays are immutable owned integer arrays. The function imports
neither GUI nor file I/O and raises `ValidationError` for invalid HSV arrays.

## Required Verification Cases

- Hand-derived primary/secondary colors, black/white/gray, and independent deterministic
  colorsys comparisons across representative RGB samples.
- Direct HSV fixtures exactly on and immediately nextafter each interval boundary; equal
  bounds; wrap (350,10); no/full selection and invalid bounds/arrays/masks.
- RGB (255,0,1) is selected by default [0,360] and excluded by [0,359].
- H=359.9 is accepted by (350,10); H=0 is accepted by (0,0), while H>0 is excluded there.
- Primaries with S=100 and white with V=100 preserve intended inclusive endpoints.
- Exact mask/result equality, shape/dtype and source immutability for every core function.

The conversion equations agree with the documented HSV formulation; float64 vectorization and
error bounds are project choices. See [research](../research.md) for primary documentation.
