# Data Model

All names below are proposed additions to existing `models.py`, not existing APIs. Append
defaulted optional fields to existing dataclasses; preserve existing positional field order.
Freeze/copy arrays using the repository's immutable-buffer pattern.

| Entity | Fields and invariants |
| --- | --- |
| AnalysisSettings | enabled bool=False; connectivity integer in {4,8}, default 8; min_area_px nonnegative integer, default 0; reject booleans as integers |
| WatershedSettings | enabled bool=False; seed_fraction finite real strictly between 0 and 1, default 0.5; background_iterations integer 0..10, default 1; kernel_size integer in {3,5,7,9}, default 3 |
| RegionStatistics | id positive integer; area_px positive integer; centroid_x/y finite source pixel coordinates; box (x,y,width,height), positive dimensions within source; contour point arrays in source coordinates |
| RegionAnalysis | source-sized int32 nonnegative labels; 0 background; raw_count >= retained_count >= 0; immutable retained statistics; filtered uint8 0/255 mask; stable row-major IDs; labels exactly identify retained regions |
| WatershedResult | status applied/empty/not_applied; reason required unless applied; source-sized int32 labels with 0 background; separate boolean boundary map; optional RegionAnalysis; uint8 foreground equals retained positive labels, excluding ridges |
| GroundTruth | normalized immutable uint8 0/255 mask; path; original SHA-256; normalized pixel hash; threshold integer 0..254; disclosed alpha rule; session_id/source hash/frame_index binding; nonnegative truth_revision |
| EvaluationResult | target baseline/components/watershed; TP/FP/FN/TN nonnegative integers totaling pixel count; IoU/Dice finite [0,1]; status normal/both_empty/one_empty; request/truth identity |

Extend ProcessingRequest with default AnalysisSettings, WatershedSettings, optional GroundTruth,
evaluation_target default baseline and settings_revision default 0. Extend SegmentationResult
with matching settings/revisions and optional analysis, separation and evaluation. Baseline
`mask`, `segmented_rgb`, `original_mask` retain existing meanings and invariant checks.
Never squeeze Watershed labels into binary-mask fields. Keep `segment()` unchanged.

Display-only contour/box/confusion toggles are GUI state and do not alter predictions. A target
may be unavailable; use absent EvaluationResult plus an explanatory GUI status, never NaN.
GroundTruth file decoding stays in I/O; construction/validation never reads a path.

## State Transitions

- Empty -> source open candidate -> complete processing -> commit; failure retains old session.
- Valid settings edit -> increment settings/request revisions -> pending -> matching commit.
  Invalid edit retains accepted settings and blocks misleading extended export/recording.
- Load truth -> pause video -> capture binding -> decode/normalize -> commit only if binding and
  truth-load revision remain current -> evaluate current target. Cancellation leaves data intact.
- Threshold/morphology/analysis edit on same frame retains truth and invalidates old metrics.
- New frame/source or explicit video restart clears truth/evaluation, including restart to frame 0.
- Target change invalidates metrics, recomputes from exact matching snapshot or shows unavailable.
- Recording captures one complete immutable snapshot; later UI changes cannot alter it.
