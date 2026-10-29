# Phase 0 Research: Grayscale, Otsu and Overlay Export

## Decision 1: Define grayscale eligibility by exact displayed RGB equality

**Decision**: A source/frame is eligible only when `R == G == B` at every pixel of the immutable
RGB snapshot. Eligibility is computed from the decoded pixels used by the application and stored
with the source identity.

**Rationale**: This directly implements FR-002, is deterministic, does not infer user intent and
allows native grayscale files that loaders expand to RGB. A single unequal pixel makes the frame
ineligible. Grayscale remains opt-in even when eligible.

**Alternatives considered**:

- A channel-difference tolerance: rejected because results would depend on an arbitrary tolerance
  and could silently classify desaturated photographs as grayscale.
- File metadata or Pillow image mode: rejected because decoded video frames and converted images
  may have no reliable original grayscale metadata.
- Automatic conversion of color sources: rejected because it is explicitly outside the feature.

## Decision 2: Implement global Otsu over the 256-value uint8 intensity domain

**Decision**: Implement Otsu as a pure NumPy function using a 256-bin histogram. Evaluate integer
thresholds `0..254` that leave both classes non-empty, maximize between-class variance, and choose
the smallest threshold among exact equal optima. Return an explicit unavailable outcome when no
candidate produces two non-empty classes. Apply polarity only after resolving the threshold:
bright is `I > T`; dark is `I <= T`.

**Rationale**: The rule is explainable, deterministic and independently testable. A smallest-tie
rule removes backend-dependent ambiguity. Separating threshold selection from polarity lets one
Otsu result drive complementary foreground interpretations.

**Alternatives considered**:

- `cv2.threshold(..., THRESH_OTSU)`: rejected for the core contract because tie behavior and
  unavailable-state semantics would be implicit in an external implementation.
- Largest or averaged tied threshold: rejected because the smallest threshold is simpler to
  describe and verify with integer fixtures.
- Adaptive/local thresholding: rejected as explicitly out of scope.

## Decision 3: Represent segmentation mode and grayscale settings explicitly

**Decision**: Extend immutable processing requests and results with `segmentation_mode` and a
validated `GrayscaleSettings` snapshot. Settings include threshold source (`manual`/`otsu`), the
manual threshold, polarity and revision. A separate `OtsuOutcome` reports applied/unavailable and
the resolved threshold without overwriting the last valid manual settings.

**Rationale**: Explicit discriminated state keeps HSV defaults backward-compatible and makes
worker completions, experiment records and GUI labels truthful. Unavailable Otsu can be reported
without fabricating a mask or mutating a prior valid result.

**Alternatives considered**:

- Reuse HSV Value bounds: rejected because a range and a one-sided intensity/polarity threshold
  have different boundary semantics and provenance.
- Encode mode in GUI booleans only: rejected because application, export and experiments could
  no longer validate or reproduce the state.

## Decision 4: Reuse the current downstream binary-mask pipeline

**Decision**: Only mask generation branches. Once an HSV or grayscale original mask exists, the
existing morphology, component analysis, Watershed, evaluation, four previews and export stages
continue unchanged.

**Rationale**: These stages consume a source-sized binary `uint8` mask and do not need to know
which selection signal produced it. This minimizes regression risk and preserves the existing
academic comparisons.

**Alternatives considered**:

- A complete parallel grayscale processing pipeline: rejected as duplicated logic and a likely
  source of semantic drift.

## Decision 5: Compose and export exact overlay pixels, not GUI screenshots

**Decision**: Centralize selection of the active overlay variant in a pure composition function.
Create an immutable `OverlaySnapshot` containing source-sized RGB pixels, variant and all relevant
source/settings/truth identities. Display and export use pixels derived from the same composition
contract. Export captures the snapshot before starting background I/O.

**Rationale**: Tk scaling, labels and display interpolation are presentation details and cannot
guarantee source resolution or pixel equality. An owned array is testable, portable and safe when
the source or overlay selection changes during a write.

**Alternatives considered**:

- Screenshot the Overlay widget: rejected because it captures display size, chrome and possible
  interpolation rather than analytical pixels.
- Recompute overlay inside the writer from mutable GUI state: rejected because async writes can
  race with frame, settings, truth and overlay changes.

## Decision 6: Add experiment schema version 3 without rewriting older records

**Decision**: Continue publishing schema 1 for baseline HSV runs and schema 2 for existing
analysis/evaluation runs. Publish schema 3 when grayscale segmentation or retained overlay
evidence is present. Add a `segmentation` object for mode/provenance and an optional `overlay`
object for variant, file hash and decoded-pixel hash. Readers keep their current schema 1/2
interpretation and explicitly validate schema 3.

**Rationale**: An additive version prevents existing records from acquiring new implied meanings.
It retains sufficient evidence to distinguish manual/Otsu results and detect changed overlays.

**Alternatives considered**:

- Add optional keys to schema 2: rejected because consumers could silently ignore required new
  provenance while still claiming full support.
- Always publish schema 3 after the feature: rejected because it would unnecessarily change
  ordinary HSV baseline records, conflicting with FR-019.

## Decision 7: Keep expensive work off Tk and preserve revision-based commits

**Decision**: Eligibility may be cached per immutable source identity. Otsu and processing run in
the existing bounded worker. Requests carry source/frame, request and settings revisions; only an
exact current completion commits. The last valid result remains visible while Otsu is unavailable
or newer work is pending.

**Rationale**: This follows the current architecture, prevents stale video-frame results and meets
the responsiveness target without an additional executor or queue.

**Alternatives considered**:

- Compute Otsu synchronously in event handlers: rejected because Full-HD frames can block Tk.
- Introduce a second worker: rejected because ordering and snapshot ownership become harder with
  no demonstrated benefit.

## Decision 8: Present intensity honestly in the existing compact workspace

**Decision**: Add compact grayscale controls near the current threshold controls: mode, manual/
Otsu source, integer threshold, polarity and availability/status. In grayscale mode the histogram
uses the intensity/Value distribution and marks Hue as unavailable rather than displaying it as a
meaningful signal. All four previews and the default-visible histogram remain.

**Rationale**: The user can understand which signal drives segmentation without expanding the
pipeline or adding another window. Existing HSV controls remain unchanged when HSV is active.

**Alternatives considered**:

- Hide the histogram: rejected because the spec requires the default-visible analytical context.
- Continue showing Hue normally: rejected because it suggests a meaningful hue measurement for
  pixels whose saturation is zero.
