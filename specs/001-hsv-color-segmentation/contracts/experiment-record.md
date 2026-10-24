# Experiment Record Contract

Local JSON schema version 1; planned writer: `src/hsv_segmentation/io/experiments.py`.
The GUI supplies a complete displayed immutable snapshot and user descriptions. This module
writes files; it does not depend on GUI classes or recompute segmentation.

## Record Shape

```json
{
  "schema_version": 1,
  "run_id": "a2b5dc79-90ad-49ad-bbd0-5a53eaa0654d",
  "created_at": "2026-10-24T08:00:00Z",
  "source": {
    "path": "../../inputs/red-object.png",
    "sha256": "64-lowercase-hex-characters",
    "media_kind": "image",
    "width": 1920,
    "height": 1080,
    "frame_index": null,
    "backend": null
  },
  "thresholds": {
    "lower_h_deg": 350,
    "upper_h_deg": 10,
    "lower_s_pct": 40,
    "upper_s_pct": 100,
    "lower_v_pct": 20,
    "upper_v_pct": 100
  },
  "lighting": "Indoor daylight beside a window",
  "observations": "Red object retained; dark shadow missed",
  "artifacts": {
    "mask": {"path": "mask.png", "sha256": "64-lowercase-hex-characters", "pixel_sha256": "64-lowercase-hex-characters"},
    "result": {"path": "result.png", "sha256": "64-lowercase-hex-characters", "pixel_sha256": "64-lowercase-hex-characters"}
  },
  "environment": {"path": "../../environment.json", "sha256": "64-lowercase-hex-characters"}
}
```

The example illustrates fields only; hash strings are explanatory, not valid evidence or a
ready-to-use experiment. Required real hashes are exactly 64 lowercase hexadecimal characters.
Threshold field suffixes specify units; enforce all bounds from data-model.md. Dimensions are
positive and match artifacts; frame_index is null for images and a nonnegative integer for
video. run_id is a UUID; created_at is UTC ISO-8601; lighting and observations are nonempty.
Unknown schema versions fail with an unsupported-version message rather than silent guessing.

## Publication

1. Create an exclusive UUID-named run directory; do not overwrite another run.
2. Validate the snapshot, descriptions, source identity/hash and environment reference.
3. Write mask.png and result.png successfully, preserving resolution and pixel values.
4. Compute source/artifact/environment hashes. Pixel hashes use the UTF-8 prefix
   `uint8|H|W|C|RGB\n` followed by C-contiguous RGB bytes for result images, or
   `uint8|H|W|1|L\n` followed by mask bytes; replace H/W/C with actual decimal dimensions
   (C=3 for RGB). No PNG metadata enters the pixel hash.
5. Write JSON to a temporary sibling record and replace record.json only after all referenced
   outputs succeed. A consumer treats only a valid published record.json as a complete run.
6. On failure, report the destination/operation, keep the live result, and do not publish a
   complete record. Orphan outputs may remain identified for retry; do not delete user sources.

Stored paths are relative to record.json where feasible; external source paths may be absolute.
Replay verifies source hash and environment availability before applying the six recorded bounds.
Do not silently substitute a similarly named source or a different video frame.

## Reproducible Evaluation

`experiments/manifest.json` lists at least 10 distinct input identities, provenance/permissions,
scene and lighting descriptions. Each input has at least two different complete threshold runs.
One photographed scene appears under at least two real lighting conditions; synthetic cases
remain explicitly labeled. `experiments/environment.json` records platform, hardware, exact
Python/Tcl/Tk/package/build versions, application revision, and video backend if used.

Automatic replay of three runs compares decoded arrays exactly, not PNG container bytes alone.
Independent student replay records participant/date, chosen runs, result and issues in
`experiments/reproduction.md`. The usability walkthrough records elapsed time and outcome.
The two human checks are pending until actually performed; preparing instructions and demo
materials does not depend on their availability. Final acceptance still requires them.
