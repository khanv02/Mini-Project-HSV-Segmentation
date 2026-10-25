# Research: HSV Color Segmentation

**Date**: 2026-10-24. Research is a design review, not execution of the application.
Official documentation supports the library behavior cited below; architecture choices,
resource policy and tolerances are project decisions. No application source was found to reuse.

## 1. Desktop Stack and Separation

**Decision**: CPython 3.11 x64, Tkinter/ttk controls, Pillow image decoding/display/export,
NumPy mathematics, OpenCV video decoding, pytest tests. Use a single src-layout package with
pure processing, file I/O, GUI and a small coordination layer.

**Rationale**: This satisfies the actual desktop/image/video requirements with understandable
modules. Tkinter is supplied with the chosen Python distribution; each external dependency
has one concrete purpose. No server, database, framework for services or Image Restoration
runtime dependency is needed. The current repository contains no reusable application modules.

**Alternatives considered**: Qt adds an external GUI dependency; HighGUI does not naturally
provide the requested organized desktop workflow. Neither is necessary for this academic scope.

**Evidence**: [Tkinter documentation](https://docs.python.org/3.11/library/tkinter.html),
[Pillow Image API](https://pillow.readthedocs.io/en/stable/reference/Image.html).

## 2. Continuous HSV and Full-Domain Hue

**Decision**: Implement the documented max/min/delta HSV equations using vectorized NumPy
float64. Pixel H is [0,360), S and V are [0,100]. Achromatic pixels have H=0 and S=0.
Lower H accepts integer 0..359; upper H accepts integer 0..360. Upper 360 is an endpoint,
not a distinct pixel color. Initial bounds are (0,360,0,100,0,100).

**Rationale**: The earlier upper bound 359 cannot include fractional hues above 359 while
also retaining direct inclusive comparisons. RGB (255,0,1) yields about 359.764705882353 degrees.
The corrected endpoint keeps six controls and makes full-domain selection explicit. Pure NumPy
float64 equations are readily explained and avoid mixing OpenCV's 8-bit and float HSV scales.
OpenCV remains necessary for video but is not the core HSV implementation.

**Alternatives considered**: Quantized 8-bit HSV conflicts with the unrounded input requirement.
A hidden special case treating (0,359) as all hues contradicts ordinary interval semantics.
A seventh all-hues switch introduces unnecessary state. Float32 conversion is possible but
unnecessary for the initial correctness-oriented academic implementation.

**Evidence**: [OpenCV conversion equations and ranges](https://docs.opencv.org/4.x/de/d25/imgproc_color_conversions.html),
[NumPy conditional selection](https://numpy.org/doc/stable/reference/generated/numpy.select.html).
The choice of float64 and the upper-control extension are project design decisions.

## 3. Numerical Verification

**Decision**: Use hand-derived primary/secondary/neutral cases and Python colorsys as an
independent scalar oracle for a deterministic sample. Conversion tolerances are circular hue
error <=1e-10 degrees and S/V absolute error <=1e-10 percentage points, with relative tolerance
zero. Construct HSV test arrays directly for exact threshold and adjacent-value tests.
Membership tests never widen intervals by the conversion-test tolerance. Masks/extracted RGB
must compare exactly. Do not round converted values to control steps.

**Rationale**: Separating numerical approximation checks from boolean interval semantics avoids
self-confirming tests and hidden color selection expansion. Vectorized production conversion
and stdlib scalar reference follow independently maintained code paths.

**Alternatives considered**: Visual checks alone cannot establish boundary correctness. Comparing
only against the same production conversion repeats implementation defects.

**Evidence**: [Python colorsys](https://docs.python.org/3.11/library/colorsys.html),
[NumPy assert_allclose](https://numpy.org/doc/stable/reference/generated/numpy.testing.assert_allclose.html).
The tolerances are chosen acceptance values for float64 and must be tested, not reported as
measurements already achieved.

## 4. GUI Work and Snapshot Ownership

**Decision**: One Tk root on the main thread; a single serialized background executor owns
file decoding and core work. Keep at most one active and one replaceable pending request.
The GUI polls plain-result messages with after(); it creates Tk images and updates widgets
only on the main thread. Each request includes session, parameter and frame revisions.

**Rationale**: Long callbacks obstruct the event loop. Revision checks prevent a late result
from being mislabeled with newer controls, and bounded queues prevent runaway memory use.
On parameter edits, obsolete results become non-exportable until a current result is displayed.
Capture the displayed immutable result, rather than rereading changing video state, for export.

**Alternatives considered**: Synchronous decoding/processing blocks interaction; a new thread
per edit creates contention and stale results. Multiprocessing is unnecessary initially.

**Evidence**: [Tkinter threading model](https://docs.python.org/3.11/library/tkinter.html#threading-model).
The bounded revision protocol is the project's application design.

## 5. Image Loading, Resource Policy and PNG Output

**Decision**: Recognize format, inspect dimensions, fully decode and normalize inside a file
context before committing a candidate source. Preserve Pillow's decompression safeguards;
convert warnings/errors into actionable input failures. Normalize supported grayscale to RGB,
ignore alpha as the spec states, and reject unsupported bit-depth/mode representations clearly.
Use a documented 12,000,000-pixel limit and catch allocation failure. Export uint8 PNG L masks
with 0/255 and PNG RGB results at original dimensions; previews never replace source arrays.

**Rationale**: Image.open is lazy, so a valid header does not prove full readability. Full decode
before session replacement preserves prior valid input. The resource limit bounds academic use
while including 1080p; it is not a universal memory guarantee. PNG preserves required pixels.

**Alternatives considered**: JPEG output can alter masks/colors. Unlimited input sizes obscure
failure behavior. Automatic resizing would invalidate source-resolution export expectations.

**Evidence**: [Pillow open/loading and safeguards](https://pillow.readthedocs.io/en/stable/reference/Image.html),
[Pillow PNG support](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#png).

## 6. Video Decoder Lifecycle and Termination

**Decision**: Require successful capture opening and first-frame decoding before source commit.
Read sequentially, convert BGR to RGB at the I/O boundary, and reopen for restart. Release the
capture on replacement, failure and shutdown. Use grab/retrieve statuses for explicit decode
failure where available, and known fixtures for normal end-of-file acceptance.

**Rationale**: A failed VideoCapture.read can mean no more frames or acquisition failure; reported
frame counts/properties are backend-dependent. A retrieve failure after a successful grab is
an explicit decode failure. Early termination before a credible known frame count is a failure.
If grab fails after frames and no reliable ending information exists, stop safely with the
honest message: "Video ended or the next frame could not be read; reopen or try a supported
encoding." Retain the last frame and allow restart. Do not label every failed read as clean EOF.

**Alternatives considered**: Loading all video frames is unbounded. Adding another decoder stack
solely to promise universal failure diagnosis increases scope without removing all ambiguity.

**Evidence**: [OpenCV VideoCapture lifecycle, read/grab/retrieve and backend properties](https://docs.opencv.org/4.13.0/d8/dfe/classcv_1_1VideoCapture.html).
The UI exposes this decoder limitation; normal EOF remains verified on known fixture files.

## 7. Packaging and Dependency Reproducibility

**Decision**: T002 writes metadata and resolves/locks third-party packages without installing
an as-yet nonexistent local package. T003 creates package skeletons, then installs the local
project and checks imports/test discovery. Pin all selected direct/transitive and build-tool
versions for the target interpreter after verifying installation. Record interpreter/Tcl/Tk
versions and decoder backend separately; use a regular install smoke check before submission.

**Rationale**: A src layout needs installation for normal imports. Correct ordering removes
the earlier bootstrap dependency contradiction. Architecture can be settled before empirical
selection of compatible pins; no unverified exact versions are fabricated in this plan.

**Alternatives considered**: PYTHONPATH workarounds hide packaging faults. Unbounded versions
or calling untested releases "latest compatible" do not support repeatable experiments.

**Evidence**: [PyPA src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/),
[Packaging projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/).

## 8. Experiment Publication and Human Acceptance

**Decision**: One versioned JSON record per run links a source hash, six thresholds/units, frame
identity, environment, notes and lossless artifacts. Write outputs to a unique run directory,
verify success, then publish the record last. Failed artifacts never yield a complete record.
Automated three-run pixel reproduction is a development check; second-student reproduction
and the five-minute usability task are separate final acceptance evidence.

**Rationale**: Output hashes and explicit environment records support the academic reproducibility
requirement with ordinary files. Documentation preparation must not wait for a participant,
while final submission still requires genuine independent evidence.

**Alternatives considered**: A database/gallery is unnecessary. A model claiming to be a second
student or marking unavailable human acceptance as passed would invalidate the evidence.

**Evidence**: Project spec FR-014/FR-015 and SC-005/SC-006; constitution Principles VII and IX.

## Resolution Status

All architecture, numerical and integration questions are resolved for this planning iteration.
Exact package pins, runtime timing, real-image provenance and participant outcomes are outputs
of implementation/validation tasks. They are not claimed to exist or pass in this research.

## 9. Clean Desktop Workspace

**Decision**: Use a light-first scientific workspace with native Segoe UI typography, neutral
slate surfaces, one blue primary action, visible focus, an 8-pixel spacing rhythm and minimal
elevation. Place threshold editing in a 300-pixel inspector and keep the three synchronized
previews in the flexible work area. Hide playback controls outside video sessions while keeping
export actions disabled until a current result exists. Use native state changes rather than
decorative animation.

**Rationale**: Image evidence and numeric bounds are the product's primary content. A stable
two-region workspace shortens eye travel, prevents the command bar from becoming a row of equal
weight actions, and remains implementable with the existing desktop toolkit and offline scope.
Semantic tokens make focus, errors and disabled states consistent without introducing a theme
dependency.

**Alternatives considered**: Glassmorphism and strong gradients reduce contrast over image-heavy
content. A dark-only developer-tool theme competes with masks and image colors. Replacing the
three simultaneous previews with tabs violates the established comparison requirement. Migrating
GUI frameworks would add risk and dependencies without changing the academic workflow.
