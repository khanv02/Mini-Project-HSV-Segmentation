# Processing Contracts

These are proposed new interfaces. Existing verified APIs are listed in research.md. Pure
functions must not import Tk, decode files, mutate inputs or depend on session globals.

| Proposed callable | Contract |
| --- | --- |
| `analyze_components(mask, settings)` | Nonempty uint8 2D 0/255 mask + AnalysisSettings -> RegionAnalysis; explicit connectivity, inclusive area filtering, background excluded |
| `analyze_labels(labels, min_area_px)` | Nonempty nonnegative int32 2D labels -> RegionAnalysis; preserve region separation, normalize IDs, derive contours/statistics without reconnecting union |
| `separate_watershed(rgb, mask, settings, min_area_px=0)` | Same-sized RGB uint8 and binary mask -> WatershedResult; copied BGR/marker buffers; preserve HSV domain; truthful status |
| `evaluate_masks(prediction, truth, *, target)` | Same-sized nonempty binary uint8 masks -> EvaluationResult counts/scores; identity attached by application |
| visualization helpers in `visualization.py` | Source plus labels/statistics or prediction/truth -> owned RGB display array; source pixels never modified |

Array dimension limit matches existing MAX_IMAGE_PIXELS. Invalid types/shapes/settings raise
existing ValidationError with field name. Resource/OpenCV errors are translated at application
boundary with recovery context. Analyze empty foreground normally; reject empty array dimensions.

Component area is exact label pixel count, centroid arithmetic mean of x/y pixel indices, box
is `(min_x,min_y,max_x-min_x+1,max_y-min_y+1)`. Retain area >= min_area_px. Contours are external
per-label boundaries; holes are not additional objects. Normalize IDs by first row-major pixel.

Watershed distance uses a zero-padded mask and L2/5 aperture; crop back to source shape. Seed
threshold is strict `distance > seed_fraction*max(distance)`. Background comes from outside
configured dilation, markers 1 background/2+ foreground/0 unknown. Fewer than two seed labels,
no known background or source dimension <3 -> not_applied; empty foreground -> empty. Return
no derived evaluable prediction for not_applied. Empty status has a valid all-zero prediction.
Successful labels/boundaries are clipped to baseline domain, ridges excluded from foreground.
`analyze_labels` preserves identities for post-separation minimum-area filtering.

For prediction P and truth G: TP=|P∩G|, FP=|P\G|, FN=|G\P|, TN=remaining pixels.
IoU=TP/(TP+FP+FN); Dice=2TP/(2TP+FP+FN). Both empty -> 1/1 with both_empty; one empty ->
0/0 with one_empty. No integer overflow in counts; Python integer arithmetic for denominators.
Compare scores at absolute tolerance 1e-12; never use selected fraction as quality.

`process_source` remains authoritative; `_CachedProcessor` delegates with existing cached
HSV/histogram arguments. Optional stages must match synchronous and asynchronous paths exactly.
