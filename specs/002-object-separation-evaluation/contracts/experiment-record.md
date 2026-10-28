# Experiment Record Contract

Retain `publish_experiment`'s existing positional arguments and baseline output semantics.
Carry optional derived data on its immutable snapshot. Disabled extensions and absent truth
continue publishing schema_version 1 as today. Any enabled analysis/separation or evaluation
publishes schema_version 2, preserving baseline source/thresholds/morphology/lighting/
observations/environment/artifacts keys and existing mask.png/result.png meanings.

Schema 2 adds `analysis` (settings, raw/retained counts, per-region area/centroid/box),
`watershed` (settings, applied/empty/not_applied status, reason and ridge convention), and
`evaluation` when valid (target, counts, scores, empty status, truth binding/conversion/provenance).
Optional fields absent mean not requested; missing data must not imply perfect/zero quality.
When separation is not applied, record its status but no fabricated labels or evaluation.

Required extension artifacts when applicable:

- `components_mask.png`: retained component foreground.
- `watershed_labels.npy`: normalized int32 nonnegative labels, saved without pickle.
- `watershed_boundaries.png`: 0/255 ridge mask within baseline domain.
- `watershed_mask.png`: retained separated foreground excluding ridge pixels.
- `prediction.png` and `ground_truth.png` for evaluated runs, exactly the evaluated masks.

Each artifact entry has relative path and file SHA-256. Binary PNGs also use existing
pixel_sha256. Labels include dtype/shape and SHA-256 over contiguous little-endian int32 bytes
with explicit dtype/shape prefix; do not call existing uint8-only pixel_sha256 on label arrays.
Ground truth includes original path/file SHA-256, normalized hash and threshold/alpha rule.
Save normalized truth in-run so reproduction does not depend on original file remaining present.

Write every required artifact before atomically publishing record.json through existing
_write_record. A partial directory may remain after failure, but must contain no complete
record; report partial location for inspection/retry. Never rewrite old runs or environment.

Add version-aware evidence generation/replay support to `scripts/generate_experiment_evidence.py`
and the existing reproduction test helpers. The generator currently publishes baseline evidence;
it is not an existing general replay API. Dispatch versions 1/2, using missing extension fields
as disabled only for version 1. Unknown
versions fail explicitly. Verify hashes before reconstructing; source/environment mismatch is
reported, not ignored. Compare derived labels/counts exactly in recorded environment and metrics
within 1e-12. Video reproduction identifies source hash and exact frame index. Object IDs are
frame-local, with no tracking meaning. External schema-1-only readers are not promised schema-2
support; preserve schema-1 files and document the new format explicitly.
