# Contract: Experiment Record Schema 3

## Compatibility

- Schema 1 and 2 structures and meanings are unchanged.
- Readers explicitly accept versions 1, 2 and 3 and continue rejecting unknown versions.
- Ordinary HSV publication still chooses schema 1 or 2 under the existing rules.
- Grayscale mode or retained overlay evidence requires schema 3.

## Required schema 3 segmentation object

```json
{
  "segmentation": {
    "mode": "grayscale",
    "threshold_source": "manual",
    "threshold": 128,
    "manual_threshold": 128,
    "polarity": "bright",
    "settings_revision": 7,
    "eligibility": {
      "rule": "exact_rgb_channel_equality",
      "eligible": true
    }
  }
}
```

For Otsu, `threshold_source` is `otsu`, `threshold` is the resolved threshold and `tie_rule` is
`smallest_optimal_threshold`. `manual_threshold` remains the preserved editable manual value.
Schema 3 HSV records, if required by overlay evidence, use `{"mode":"hsv"}` and retain the
existing top-level HSV `thresholds` object.

## Optional overlay evidence

```json
{
  "overlay": {
    "variant": "confusion",
    "display_settings": {},
    "artifact": {
      "path": "overlay.png",
      "sha256": "<encoded-file-sha256>",
      "pixel_sha256": "<decoded-rgb-pixel-sha256>"
    },
    "truth_pixel_sha256": "<required-for-confusion>"
  }
}
```

The artifact is written from the captured `OverlaySnapshot`. Its variant and identity must match
the current result snapshot supplied to experiment publication. A confusion overlay requires the
matching ground-truth identity.

## Reproduction checks

For a grayscale record, a verifier must:

1. Resolve and hash the retained source/frame.
2. Confirm exact RGB channel equality.
3. For manual, use the recorded threshold. For Otsu, recompute with the recorded tie rule and
   require the same resolved threshold.
4. Apply recorded polarity and downstream settings.
5. Require exact mask pixel hash and, when present, exact overlay pixel hash.

Any mismatch is reported as evidence drift; it is not silently accepted.
