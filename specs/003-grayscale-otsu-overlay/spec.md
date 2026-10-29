# Feature Specification: Grayscale Segmentation, Otsu Assistance and Overlay Export

**Feature Branch**: `[003-grayscale-otsu-overlay]`

**Created**: 2026-10-30

**Status**: Draft

**Input**: User description: "Add an explicit grayscale workflow with manual intensity
thresholding, optional Otsu threshold selection, and the ability to save the displayed Overlay.
Keep HSV segmentation as the default and do not include adaptive thresholding in this feature."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Segment a Grayscale Image by Intensity (Priority: P1)

As a student, I want an explicit grayscale mode so that I can segment dark or bright regions
without treating Hue as meaningful color information.

**Why this priority**: Grayscale inputs are already accepted, but the color-oriented controls
make the correct workflow difficult to discover and explain during a demonstration.

**Independent Test**: Open a lossless grayscale image, opt into Grayscale Mode, choose bright
or dark foreground, adjust the intensity threshold, and verify the mask against an analytical
reference without enabling Otsu or exporting an overlay.

**Acceptance Scenarios**:

1. **Given** an image whose color channels are equal at every pixel, **When** the user enables
   Grayscale Mode, **Then** the interface identifies intensity as the active selection signal,
   does not present Hue as meaningful, and retains all four synchronized previews.
2. **Given** Grayscale Mode with bright foreground, **When** the user sets threshold `T`,
   **Then** only pixels strictly brighter than `T` are selected.
3. **Given** Grayscale Mode with dark foreground, **When** the user sets threshold `T`,
   **Then** pixels at or below `T` are selected and the chosen polarity is visible.
4. **Given** an ordinary color image, **When** the user requests Grayscale Mode, **Then** the
   mode is not applied and the user sees why the source is ineligible; the current HSV result
   remains unchanged.

---

### User Story 2 - Use Otsu as an Optional Threshold Suggestion (Priority: P2)

As a student, I want Otsu to propose a global intensity threshold so that I can compare an
automatic, explainable threshold with my manual choice.

**Why this priority**: Otsu adds academic value for grayscale demonstrations while remaining a
small, deterministic alternative that does not replace the default HSV workflow.

**Independent Test**: On a known two-level grayscale fixture, request Otsu, verify the reported
threshold and resulting mask exactly, switch back to manual thresholding, and confirm that no
color workflow or export behavior changed.

**Acceptance Scenarios**:

1. **Given** an eligible grayscale image containing separable intensity groups, **When** Otsu
   is requested, **Then** one global threshold is reported, applied with the selected polarity,
   and clearly labeled as Otsu-derived.
2. **Given** an Otsu result, **When** the user returns to manual thresholding, **Then** the user
   can edit the intensity threshold again without reopening the source.
3. **Given** a constant-intensity image, **When** Otsu is requested, **Then** the application
   reports that no meaningful split exists and preserves the last valid mask and settings.
4. **Given** a color source or unavailable current frame, **When** Otsu is requested, **Then**
   no result is fabricated and the existing result remains usable.

---

### User Story 3 - Save the Current Overlay (Priority: P2)

As a student, I want to save exactly what is shown in the Overlay preview so that reports can
include segmentation tint, object annotations, Watershed regions, or TP/FP/FN evidence.

**Why this priority**: Overlay is now a dedicated preview, but users cannot yet retain that
visual evidence through the normal export workflow.

**Independent Test**: Display each supported overlay type, save it, decode the saved image, and
verify exact pixel agreement with the Overlay preview captured by the export action.

**Acceptance Scenarios**:

1. **Given** a current segmentation overlay, **When** the user chooses Save Overlay, **Then** a
   lossless image matching the displayed Overlay is written at source resolution.
2. **Given** contours, boxes, Watershed regions, or TP/FP/FN are displayed, **When** Save Overlay
   is invoked, **Then** the saved artifact contains that exact overlay variant rather than the
   plain segmented result.
3. **Given** no valid Overlay is available, **When** the user attempts export, **Then** the
   action is unavailable or produces a recoverable explanation without creating a misleading file.
4. **Given** an export is pending, **When** the displayed source, frame, settings, truth, or
   overlay selection changes, **Then** the saved artifact still corresponds to the snapshot
   captured when export began, or the stale export is rejected explicitly.

---

### User Story 4 - Reproduce Grayscale and Overlay Evidence (Priority: P3)

As a student preparing an academic report, I want grayscale settings, Otsu provenance, polarity,
and overlay identity recorded so that another person can understand and reproduce the result.

**Why this priority**: A correct interactive result is useful first; reproducibility is required
before the feature can support retained academic evidence.

**Independent Test**: Record one manual grayscale run and one Otsu run, reconstruct their masks
from the retained source and settings, and verify their exported overlay identities and hashes.

**Acceptance Scenarios**:

1. **Given** a manual grayscale result, **When** an experiment is recorded, **Then** the mode,
   threshold, polarity, prediction identity, and relevant artifacts are retained.
2. **Given** an Otsu result, **When** an experiment is recorded, **Then** the record distinguishes
   the computed threshold from a manual threshold and contains enough evidence to reproduce it.
3. **Given** an existing HSV experiment, **When** it is replayed after this feature is added,
   **Then** its interpretation and baseline artifacts remain unchanged.

### Edge Cases

- A grayscale image is completely black, completely white, or constant at another intensity.
- A source is nearly gray but contains at least one pixel with unequal color channels.
- The chosen threshold is at the minimum or maximum supported boundary.
- Bright and dark foreground polarities produce complementary masks at the same threshold,
  including the documented equality boundary.
- Otsu has multiple thresholds with the same optimum; the chosen tie behavior must be
  deterministic and documented.
- The source or video frame changes while Otsu computation or overlay export is pending.
- The Overlay changes between segmentation tint, annotations, Watershed, and confusion display.
- The user cancels an overlay export or chooses an unwritable destination.
- Grayscale Mode is combined with morphology, object analysis, ground-truth evaluation, or video.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST keep HSV segmentation as the default mode for every newly opened
  source and MUST NOT switch to Grayscale Mode automatically.
- **FR-002**: The system MUST identify a source as grayscale-eligible only when its displayed
  color channels are equal at every pixel; eligibility MUST be deterministic and visible.
- **FR-003**: Users MUST be able to opt into and leave Grayscale Mode without reopening the source.
- **FR-004**: Grayscale Mode MUST present intensity as the active selection dimension and MUST
  communicate that Hue is not meaningful for the current source.
- **FR-005**: Manual grayscale selection MUST expose one validated whole-number intensity
  threshold and an explicit bright-foreground or dark-foreground polarity.
- **FR-006**: Bright foreground MUST use the rule `intensity > threshold`; dark foreground MUST
  use the complementary rule `intensity <= threshold`.
- **FR-007**: Grayscale Mode MUST produce a binary mask compatible with the existing morphology,
  preview, analysis, evaluation, video-frame, export, and experiment workflows.
- **FR-008**: Users MUST be able to request one global Otsu threshold only for an eligible current
  grayscale source or paused grayscale video frame.
- **FR-009**: An Otsu request MUST report the resulting threshold, the active polarity, and that
  the threshold was computed rather than manually entered.
- **FR-010**: Otsu threshold selection MUST be deterministic; ties MUST resolve using one
  documented rule and reference fixtures MUST reproduce the same threshold and mask exactly.
- **FR-011**: A source with no meaningful intensity split MUST produce an explicit unavailable
  status and MUST preserve the last valid settings and result.
- **FR-012**: Users MUST be able to return from Otsu to an editable manual threshold without
  reopening the source or changing HSV defaults for later sources.
- **FR-013**: Users MUST be able to save the current Overlay as a lossless image at the exact
  source dimensions.
- **FR-014**: Save Overlay MUST capture the displayed overlay variant: segmentation tint,
  object annotations, Watershed regions, or TP/FP/FN confusion evidence.
- **FR-015**: Save Overlay MUST NOT change the meanings or artifacts of Save Mask and Save Result.
- **FR-016**: Overlay export MUST use an immutable current snapshot and MUST reject or truthfully
  report stale, unavailable, cancelled, and failed writes without corrupting prior artifacts.
- **FR-017**: Grayscale experiments MUST retain mode, threshold source (manual or Otsu), threshold
  value, polarity, source/frame identity, mask identity, and settings needed for reproduction.
- **FR-018**: Recorded overlay evidence MUST identify its overlay variant and retain integrity
  information sufficient to detect changed pixels or files.
- **FR-019**: Existing HSV image/video behavior, numeric conventions, exports, and experiment
  records MUST remain usable and unchanged when Grayscale Mode is not selected.
- **FR-020**: User-facing documentation MUST explain grayscale versus binary images, manual
  intensity selection, foreground polarity, Otsu limitations, and the distinction between
  Result and Overlay.
- **FR-021**: Adaptive/local thresholding, automatic conversion of color photographs to
  grayscale, machine learning, and automatic mode switching MUST remain outside this feature.

### Key Entities

- **Segmentation Mode**: The explicit current selection workflow, either the existing HSV mode
  or opt-in grayscale intensity mode.
- **Grayscale Settings**: Manual or Otsu threshold source, intensity threshold, foreground
  polarity, and the source/frame revision to which they apply.
- **Otsu Outcome**: Computed threshold or unavailable status, deterministic tie outcome, source
  identity, and evidence that the result belongs to the current grayscale pixels.
- **Overlay Snapshot**: Exact source-sized RGB pixels currently represented by Overlay, its
  variant, and the source/settings/truth identities from which it was composed.
- **Grayscale Experiment Evidence**: Reproducible settings, identities, hashes, prediction, and
  optional overlay artifact associated with one recorded run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time user can open an eligible grayscale image, select bright or dark
  foreground, produce a visible manual mask, and save it in at most three minutes using the
  documented workflow.
- **SC-002**: All analytical grayscale fixtures, including threshold boundaries and both
  polarities, produce exact expected binary masks with zero mismatched pixels.
- **SC-003**: All Otsu reference fixtures produce the documented threshold and exact expected
  mask on repeated runs; constant-image cases are reported unavailable in 100% of tests.
- **SC-004**: Every supported Overlay variant saves at source dimensions with pixels exactly
  matching the snapshot displayed when export began.
- **SC-005**: Manual and Otsu experiment evidence reproduces threshold, polarity, prediction,
  and overlay identity exactly in the recorded environment.
- **SC-006**: All pre-existing automated HSV, image, video, evaluation, export, and replay tests
  pass unchanged when Grayscale Mode is not selected.
- **SC-007**: During 100 repeated Full-HD grayscale threshold changes, at least 95 results become
  current within one second and all scheduled responsiveness checks complete within 250 ms while
  processing is pending.
- **SC-008**: In a documented demonstration, users correctly distinguish grayscale input,
  binary mask, Result, and Overlay without any accuracy claim when no ground truth is loaded.

## Assumptions

- Grayscale eligibility means exact equality of the three displayed color channels at every
  pixel; nearly gray color photographs remain in HSV mode.
- Grayscale Mode is opt-in even for an eligible source so existing behavior remains predictable.
- Otsu is a single global intensity threshold intended for bimodal or approximately bimodal
  grayscale distributions; it is not promised to handle uneven illumination.
- Bright foreground is the initial polarity when Grayscale Mode is first enabled; users may
  explicitly choose dark foreground.
- Overlay export uses the same lossless image family and overwrite/cancellation expectations as
  existing image exports.
- The existing four-preview workspace, ground-truth evaluation, and experiment lifecycle are
  available dependencies and retain their current meanings.
