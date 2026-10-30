# HSV segmentation algorithm

This document describes the equations and conventions implemented by
`src/hsv_segmentation/processing/`. The processing layer accepts in-memory arrays only;
it does not import Tk, open files, or resize the source.

## Input and units

An input is a non-empty NumPy `uint8` RGB array with shape `(height, width, 3)` and at
most 12,000,000 pixels. Channel order is red, green, blue. Each channel is normalized
to `[0,1]` in `float64` before conversion. The output HSV array is also `float64`:

- hue `H` is measured in degrees in `[0,360)`;
- saturation `S` is a percentage in `[0,100]`; and
- value `V` is a percentage in `[0,100]`.

Pillow performs file decoding at the I/O boundary. Eight-bit grayscale is replicated
into R, G, and B. LA and RGBA alpha channels are ignored rather than composited, palette
images are converted to RGB, and supported RGB PNG/JPEG/BMP data reaches this algorithm
as three-channel `uint8`. Processing and exported results keep source dimensions.

## RGB to HSV conversion

For normalized channels `r`, `g`, and `b`, define:

```text
Cmax  = max(r, g, b)
Cmin  = min(r, g, b)
delta = Cmax - Cmin
V     = 100 * Cmax
S     = 0                         when Cmax = 0
        100 * delta / Cmax        otherwise
```

Hue is zero for an achromatic pixel (`delta = 0`). Otherwise the implementation uses
the first matching maximum channel in R, G, B order:

```text
H' = ((g - b) / delta) mod 6      when Cmax = r
H' = ((b - r) / delta) + 2        when Cmax = g
H' = ((r - g) / delta) + 4        when Cmax = b
H  = (60 * H') mod 360
```

Equality tests between a maximum and a channel are exact because both values come from
the same normalized array. Division is performed only where its denominator is nonzero.
There is no epsilon, integer quantization, or rounding before threshold membership.

Black, white, and gray pixels are neutral: `H = 0`, `S = 0`, while `V` retains their
brightness percentage. Consequently, a range containing `H=0` and `S=0` can select
neutral pixels; hue alone is not meaningful for them.

## Six inclusive controls

The user supplies six integers. Lower hue is `0..359`, upper hue is `0..360`, and all
S/V bounds are `0..100`. S and V require lower <= upper. Hue deliberately permits a
reversed pair to express an interval crossing red at zero.

For an ordered hue pair (`lower_h <= upper_h`):

```text
hue_selected = lower_h <= H <= upper_h
```

For a wrapped pair (`lower_h > upper_h`):

```text
hue_selected = H >= lower_h OR H <= upper_h
```

The final mask is the conjunction of hue selection and the inclusive S and V intervals:

```text
selected = hue_selected
           AND lower_s <= S <= upper_s
           AND lower_v <= V <= upper_v
```

Selected pixels receive mask value 255; all others receive 0. The segmented result
copies the original RGB value at mask 255 and writes black `(0,0,0)` elsewhere. The
default `(H 0..360, S 0..100, V 0..100)` therefore selects the complete hue domain.
Although 360 is a valid upper endpoint, converted pixel hues are always less than 360.

## HSV histogram aid

The optional histogram panel summarizes the current decoded image or video frame; it does not
change segmentation. Hue uses 360 one-degree bins (`floor(H)`), while saturation and value use
101 one-percentage-point bins (`floor(S)` and `floor(V)`). Exact S/V value 100 is therefore
stored in bin 100. Counts are integers and each S/V histogram totals the source pixel count.

Hue is visually unstable for near-neutral colors, so the hue chart includes only pixels whose
unrounded saturation is at least 5%. The panel reports the excluded count explicitly, and the
hue-bin total plus that count equals the source pixel count. This fixed display cutoff applies
only to the hue chart: it does not remove pixels from S/V charts, alter HSV values, or affect the
mask. In particular, S=5.9 belongs to display bin 5 but is not selected by the exact threshold
interval S=5..5.

Red overlays show the six active threshold values on continuous H 0..360 and S/V 0..100 axes;
they do not snap to bar boundaries. An equal lower/upper pair is drawn as a labeled line, and a
wrapped hue interval is drawn at both ends of the hue axis. The charts are a manual selection
aid only. The application does not infer thresholds and does not implement Otsu or another
automatic thresholding method. Counts are cached by accepted source/frame identity, while an
edit updates only the overlay until its matching segmentation result is published.

## Precision, reproducibility, and limitations

Conversion and comparisons use NumPy `float64`. Tests compare analytical and independent
`colorsys` references with circular hue error at most `1e-10` degrees and S/V absolute
error at most `1e-10` percentage points. Mask and extracted RGB comparisons are exact.
Immutable snapshots prevent later caller changes from altering a recorded result.

HSV thresholding is deterministic and easy to explain, but it is not object recognition.
It cannot distinguish different objects with overlapping colors, and shadows, highlights,
white balance, compression artifacts, reflections, and illumination changes can move pixels
across fixed thresholds. Hue is unstable when saturation is near zero. The application does
not denoise, learn thresholds, track objects, estimate accuracy without ground truth, process
audio, or encode a complete output video. Preview images may be resized for display, while
processing, masks, experiment artifacts, and exports remain at source resolution.

## Object analysis and minimum-area filtering

Object analysis is derived from the current binary HSV mask after optional morphology.
Connected components use configurable 4- or 8-neighbor connectivity. Each retained region
reports exact foreground-pixel area, centroid, and an axis-aligned bounding box. The filter is
inclusive: a region is retained when `area_px >= minimum_area_px`. Region IDs are stable in
row-major discovery order. Contours are display geometry only; their polygon area is not used
as pixel area. A component is a connected mask region, not a guaranteed real-world object.

## Optional distance transform and Watershed

Watershed is a post-processing step, never a replacement for thresholding. It starts from the
HSV/Grayscale mask after morphology and computes an L2 distance transform. Local distance-peak
plateaus define independent markers. Each foreground pixel is associated with its nearest peak;
the configured seed-core fraction then thresholds distance relative to that local peak height,
not the global maximum. This prevents a large object from suppressing a smaller object's marker.
OpenCV Watershed runs on a copy of the source image. Positive labels and boundary ridges are
clipped back to the baseline mask; minimum-area filtering is applied after splitting.

At least two local-peak markers and some known background are required. Empty masks
produce `empty`; insufficient markers produce `not_applied` with a reason, and the baseline
HSV result remains available. Marker-controlled Watershed is image-dependent and does not
guarantee separation of every touching or overlapping-looking object. Processing is also
bounded to 2,048 local markers: a noisier mask returns `not_applied` before Watershed and
per-region contour analysis to prevent unbounded CPU and memory use.

## Ground truth, IoU, and Dice

Ground truth is normalized to a binary mask using the strict rule `gray > threshold`. It must
be a lossless PNG/BMP with the same source dimensions; alpha is ignored and RGB channels must
be equal. The selected prediction can be baseline, area-filtered components, or an applied
Watershed union.

```text
IoU  = TP / (TP + FP + FN)
Dice = 2 TP / (2 TP + FP + FN)
```

Both-empty masks score 1.0 and receive an explicit `both_empty` status; exactly one empty mask
scores 0.0. TP is green, FP red, and FN blue in the optional confusion view. The displayed
percentage of selected pixels is coverage only and must never be interpreted as accuracy.

