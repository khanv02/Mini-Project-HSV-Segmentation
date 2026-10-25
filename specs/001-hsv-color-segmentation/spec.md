# Feature Specification: HSV Color Segmentation

**Feature Branch**: No feature branch created; feature location is independent of branch name.

**Created**: 2026-10-24

**Status**: Draft

**Input**: User description: Build an independent desktop academic application named
"HSV Color Segmentation" to open images and videos, interactively select HSV color thresholds,
visualize masks and extracted regions, save results, and evaluate at least 10 test images.
Reuse existing GUI and utility components where feasible. Object counting, tracking, and
machine learning are outside the initial scope.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Segment an Image Interactively (Priority: P1)

As a student, I want to open an image and adjust color thresholds while comparing the original,
mask, and extracted regions so that I can understand and demonstrate HSV segmentation.
HSV means hue (color angle), saturation (color intensity), and value (brightness).

**Why this priority**: This is the primary algorithm and provides a complete image demonstration.

**Independent Test**: Open a known color test image, change each of the six thresholds, and
verify the selected pixels and all three views without needing video or experiment recording.

**Acceptance Scenarios**:

1. **Given** a newly opened application, **When** the student opens a valid supported image,
   **Then** the original, binary mask, and segmented result appear with labels, and the six
   current threshold values and their allowed ranges are visible.
2. **Given** a displayed image, **When** any threshold changes to a valid value, **Then** the
   mask and extracted result update automatically for those values, without reopening the file.
3. **Given** a color test image with known HSV values, **When** thresholds include some pixels
   and exclude others, **Then** the mask is white exactly at included pixels, black elsewhere,
   and the extracted result preserves included colors with excluded pixels black.
4. **Given** valid thresholds, **When** an entry is nonnumeric or outside its allowed range,
   or the saturation or value lower limit exceeds its upper limit, **Then** the application
   explains the error and does not apply or export results labeled with the invalid values.
5. **Given** colors on either side of the hue origin, **When** the lower hue exceeds the upper
   hue, **Then** the selected interval crosses the hue origin and includes both end segments.
6. **Given** a displayed input, **When** the student compares the three labeled views,
   **Then** they show the same source at matching proportions with no source modification.

---

### User Story 2 - Save Results for a Report (Priority: P2)

As a student, I want to save the binary mask and extracted color result so that I can include
reliable evidence in a report or presentation.

**Why this priority**: Saved evidence makes the primary workflow useful beyond the live GUI.

**Independent Test**: With a known image result displayed, export both outputs and reopen them
to verify dimensions, binary mask values, and extracted colors.

**Acceptance Scenarios**:

1. **Given** a current valid result, **When** the student saves the mask or segmented result,
   **Then** the selected output is saved at the source resolution and success identifies its path.
2. **Given** an existing destination file, **When** saving would overwrite it, **Then** the
   application requests overwrite confirmation and cancellation leaves that file unchanged.
3. **Given** an unwritable destination, **When** the student attempts to save, **Then** a clear
   error identifies the failed operation without losing the current input or result.
4. **Given** no input or an incomplete result update, **When** the student attempts an export,
   **Then** saving is unavailable until a complete, valid result is available.
5. **Given** a valid snapshot and a deliberately delayed write, **When** saving starts,
   **Then** the window continues handling interaction, duplicate save/record requests are
   disabled until completion, and completion reports the captured output path or failure.

---

### User Story 3 - Segment Video Frames (Priority: P2)

As a student, I want to open and play a video, pause it, and adjust thresholds so that I can
observe how the same color selection behaves as the scene changes.

**Why this priority**: Video input is required, while image segmentation remains the core demo.

**Independent Test**: Open a short supported video, play and pause it, modify thresholds, and
verify synchronized views and an exported paused-frame result.

**Acceptance Scenarios**:

1. **Given** a supported readable video, **When** it opens, **Then** the first readable frame
   and its mask and segmented result appear with the frame position.
2. **Given** an opened video, **When** playback starts or pauses, **Then** all three views
   refer to the same frame, and pausing retains that frame for inspection.
3. **Given** a playing or paused video, **When** valid thresholds change, **Then** subsequent
   displayed results use the new thresholds; a paused frame is reprocessed without resuming.
4. **Given** a video at its end, **When** playback completes, **Then** it stops cleanly, retains
   the last valid frame, and allows playback to restart from the beginning.
5. **Given** video input, **When** the student saves a result, **Then** the application captures
   one consistent displayed frame and its thresholds, and exports that frame's mask or result.

---

### User Story 4 - Record and Compare Experiments (Priority: P3)

As a student, I want to record input identities, thresholds, outputs, and observations for at
least 10 test images so that I can explain segmentation quality and lighting sensitivity.

**Why this priority**: Reproducible comparisons support the academic evaluation of the algorithm.

**Independent Test**: Use a 10-image collection, record two threshold settings per image, and
reproduce selected records using their input identities and saved threshold values.

**Acceptance Scenarios**:

1. **Given** a valid result, **When** the student records an experiment, **Then** a local record
   includes the source identity, frame position if applicable, six thresholds with units,
   lighting description, observations, and references to the saved mask and result.
2. **Given** at least 10 distinct test images, including a scene photographed under at least
   two lighting conditions, **When** two threshold sets per image are recorded, **Then** the
   records distinguish every run and allow the original and saved outputs to be compared.
3. **Given** a recorded experiment and its source, **When** another student reapplies the
   recorded thresholds under the recorded experiment conditions, **Then** the same mask and
   extracted pixel values are obtained.
4. **Given** saved comparison outputs, **When** preparing an academic presentation, **Then**
   the student can identify missed target regions, unwanted selected regions, and effects of
   threshold or lighting changes using the labeled source and outputs.

---

### User Story 5 - Recover from Invalid Input (Priority: P2)

As a student, I want understandable file errors and a clear desktop layout so that mistakes do
not interrupt my demonstration or require restarting the application.

**Why this priority**: Reliable input handling is necessary for every demonstration.

**Independent Test**: Try unsupported, missing, and corrupt files, cancel a file dialog, then
open a valid file and confirm normal operation.

**Acceptance Scenarios**:

1. **Given** the desktop window, **When** the student locates the main controls, **Then** file
   input, HSV parameters, and result visualization occupy distinct labeled sections.
2. **Given** an unsupported, missing, unreadable, or corrupt input, **When** opening fails,
   **Then** an actionable message identifies the problem and the previous valid input remains.
3. **Given** an open or save dialog, **When** the student cancels it, **Then** the current
   input, thresholds, results, and existing files remain unchanged.

### User Story 6 - Inspect HSV Distributions (Priority: P2)

As a student, I want to inspect the hue, saturation, and value distributions of the displayed
image or video frame so that I can choose HSV bounds with visual evidence rather than guessing.

**Why this priority**: Distribution charts explain how the current source relates to the six
manual bounds, while keeping the validated threshold-membership algorithm unchanged.

**Independent Test**: Open a synthetic image with known HSV components, display the histogram
panel, and compare every bin and excluded low-saturation hue count with hand-derived values.
Move ordered and wrapped threshold bounds and verify the source bin counts stay unchanged,
the overlays follow the active bounds, and segmentation follows the original six-bound rules.

**Acceptance Scenarios**:

1. **Given** a loaded still image or current video frame, **When** the histogram panel is shown,
   **Then** it presents three labeled frequency charts with hue bins of one degree and
   saturation/value bins of one percentage point, alongside all three result views.
2. **Given** pixels with saturation below 5 percent, **When** the hue chart is computed,
   **Then** those pixels are excluded from hue bins and their count is reported; all pixels
   remain included in saturation and value charts.
3. **Given** a valid threshold edit, **When** the new values become active, **Then** the charts
   update their selected-range overlays immediately; a wrapped hue interval is highlighted on
   both ends of the hue axis, without changing segmentation semantics.
4. **Given** a source replacement or video frame advance, **When** the accepted source/frame
   changes, **Then** all three distributions update to match that exact source/frame and no
   stale chart is labeled as current.
5. **Given** the histogram panel is opened or closed, **When** the student compares the result,
   **Then** the original, binary mask, and segmented result remain available and synchronized.
6. **Given** equal lower and upper bounds, **When** the corresponding interval is displayed,
   **Then** it appears as a labeled boundary line at that numeric value rather than shading an
   entire histogram bin. For example, S=5.9 belongs to bin 5 but is excluded by S=5..5.
7. **Given** a 960 by 640 pixel application client area at 100% display scaling, **When** the
   histogram panel is shown, **Then** all three charts, their labels and interval markers, the
   six HSV controls and panel toggle are visible without overlap or scrolling; each of the three
   result views retains at least a 160 by 120 pixel preview area with aspect-preserving fitting.

---

### User Story 7 - Work in a Clean Analysis Workspace (Priority: P1)

As a student, I want the controls to be visually organized around the segmentation workflow so
that I can find the next action quickly, concentrate on the images, and demonstrate the tool
without being distracted by inactive or unrelated controls.

**Why this priority**: The workspace is the entry point for every image, video, histogram and
experiment workflow; unclear hierarchy increases demonstration time and error risk even when the
underlying processing is correct.

**Independent Test**: Start at the empty application, open an image, then a video, edit all HSV
bounds, show the histogram and operate the window at 960 by 640 and at a large desktop size.
Verify that controls follow the current context, all three previews remain usable, and keyboard
focus and status feedback remain visible.

**Acceptance Scenarios**:

1. **Given** a newly opened application, **When** no media is loaded, **Then** opening actions
   are visually primary, output and experiment actions are unavailable, and video playback
   controls do not compete with the empty-state workflow.
2. **Given** an image or video is loaded, **When** the student scans the workspace, **Then** file
   actions, HSV controls, visualization tools and status feedback form distinct, consistently
   spaced regions with the previews receiving the largest share of the window.
3. **Given** the student edits thresholds, **When** they move between hue, saturation and value,
   **Then** each channel presents its lower and upper bound as one recognizable group with visible
   units, current values and validation feedback.
4. **Given** an image is active, **When** the interface is shown, **Then** video-only playback
   controls are hidden; **Given** a video is active, **When** its state changes, **Then** the
   appropriate playback controls and frame position appear without moving the preview region.
5. **Given** the application is operated with a keyboard, **When** focus moves through interactive
   controls, **Then** the focus indicator is visible, traversal follows the visual workflow, and
   the primary open actions have documented shortcuts.
6. **Given** a 960 by 640 client area or a large desktop window, **When** the histogram is shown
   or hidden, **Then** there is no overlapping text or horizontal whole-window scrolling, all
   three previews remain simultaneously available, and each retains at least a 160 by 120 pixel
   drawable area.

### Edge Cases

- No selected pixels produces an all-black mask and result; selecting all pixels produces an
  all-white mask and an unchanged color result. Neither condition is an error.
- Pixels equal to any threshold boundary are included. Equal lower and upper values select
  that value alone, including when the two hue values are equal.
- A hue interval crossing zero is valid; reversed saturation or value intervals are invalid.
- Achromatic pixels follow the documented HSV conversion convention; hue alone cannot distinguish
  neutral pixels, so saturation and value remain available to refine selection.
- Grayscale and transparent images are handled according to the documented normalization rule
  in Assumptions; unsupported image representations receive an explicit error.
- Rapid threshold changes must not leave a stale result presented as the latest result.
- Replacing an input during playback stops the old playback; no old frames appear as new input.
- Empty videos fail to open; a decoding failure during playback stops with an error and keeps
  the last valid frame. Unsupported video encoding receives an explicit message.
- Large inputs may take longer; the window remains usable, and display fitting does not change
  processing or export resolution. Inputs beyond available resources fail with a useful error.
- A failed experiment export must not report a complete record when referenced outputs failed
  to save; the student can retry without losing the displayed result.
- Without loaded media, the histogram panel shows an empty state. If every pixel has S < 5%,
  the hue chart has zero counts and reports every pixel as excluded; the S and V charts remain
  populated. A failed source open preserves the previous charts with the previous valid session.
- Invalid or pending threshold text must not be presented as active histogram intervals; overlays
  identify the last valid threshold set and share the result's invalid/pending status.
- Resizing between the supported minimum and a large desktop size must preserve control order,
  avoid clipped action labels, and keep status text separate from primary actions.
- Contextual controls must not retain focus after they are hidden, and hiding image-only or
  video-only actions must not change the current media, thresholds, result or playback state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST provide a desktop GUI named "HSV Color Segmentation" with
  distinct sections for file input, HSV controls, and labeled result visualization.
- **FR-002**: Users MUST be able to open local PNG, JPEG, and BMP images and locally decodable
  MP4 and AVI video files. Available formats and video encoding limitations MUST be documented.
- **FR-003**: Opening an input MUST display its original image or first readable video frame
  and initialize the corresponding mask and segmented result using the visible thresholds.
- **FR-004**: The application MUST derive segmentation from the input's HSV representation
  using explicit lower and upper limits for hue, saturation, and value.
- **FR-005**: The GUI MUST expose all six integer threshold values and units:
  lower hue from 0 to 359 degrees, upper hue from 0 to 360 degrees, and integer saturation
  and value from 0 to 100 percent, inclusive. Upper hue 360 is an interval endpoint only.
- **FR-006**: A pixel MUST be selected exactly when all three HSV components lie in their
  inclusive intervals. A reversed hue interval MUST select hues at or above the lower limit
  or at or below the upper limit; saturation and value intervals MUST remain ordered.
- **FR-007**: The binary mask MUST contain only selected and unselected values, rendered white
  and black respectively. The extracted result MUST preserve selected source colors and render
  unselected pixels black without changing source dimensions or modifying the source file.
- **FR-008**: Every valid parameter change MUST automatically update the results. Invalid
  entries MUST produce specific range or ordering feedback and MUST NOT become active settings.
- **FR-009**: The original, mask, and extracted result MUST be simultaneously available for
  before-and-after comparison, retain aspect ratio, and refer to the same input or video frame.
- **FR-010**: Video input MUST support play, pause, end-of-file stop, and restart. The current
  frame position MUST be visible, and threshold changes MUST also work while paused.
- **FR-011**: Users MUST be able to save masks and segmented results as lossless PNG images
  at source resolution. A saved mask MUST contain only intensity values 0 and 255. A video
  export MUST correspond to one identified displayed frame and one complete threshold set.
- **FR-012**: Saving MUST identify success or failure, request confirmation before overwrite,
  and prevent export of missing, invalid, or incomplete results. PNG encoding, hashing and
  experiment JSON writing MUST run outside the GUI event handlers on a captured immutable
  snapshot; the window MUST continue handling interaction while writing is pending.
- **FR-013**: Invalid or unsupported files, decoding failures, and write failures MUST produce
  messages identifying the failed operation, affected file or parameter, cause category,
  preserved session state, and at least one concrete corrective action. Unknown decoder causes
  MUST be described as uncertain rather than asserted as known. Parameter errors MUST include
  the allowed range or ordering rule. Exact wording may vary; these contents are testable.
  Open failures MUST preserve the previous valid session; cancellation MUST preserve session state.
- **FR-014**: Users MUST be able to persist an experiment record with source identity, frame
  position where applicable, all six threshold values and units, date, lighting description,
  qualitative observations, and links or paths to successfully saved mask and result images.
- **FR-015**: The project MUST provide a reproducible demonstration using at least 10 distinct
  test images, with two threshold sets per image and at least one scene under two lighting
  conditions. Input provenance, environment versions, procedure, and expected observations
  MUST accompany the records so another student can repeat the comparison.
- **FR-016**: The application MUST run its full input, segmentation, visualization, export,
  and experiment workflow independently of the Image Restoration project and network services.
- **FR-017**: Algorithm explanations and automated correctness checks MUST cover HSV conversion,
  inclusive interval selection, hue wraparound, and extraction, including boundary and invalid
  cases. Core processing MUST be verifiable without operating the GUI, as the constitution requires.
- **FR-018**: The application MUST provide an optional HSV histogram panel for the current image
  or video frame. It MUST show 360 one-degree hue bins and 101 one-percentage-point bins each for
  saturation and value. Hue counts MUST exclude pixels with saturation below 5 percent, and the
  excluded count MUST be visible; saturation and value counts MUST include every pixel. The panel
  MUST overlay current valid threshold intervals, show wrapped hue as both end intervals, update
  on accepted source/frame changes and valid threshold edits, and MUST NOT itself change
  thresholds or segmentation results. Counts MUST describe the complete source/frame rather
  than just mask-selected pixels. Viewing or hiding the panel MUST preserve all three result
  views. Each nonnegative component value belongs to the bin labeled by its integer part;
  saturation/value equal to 100 belong to the final bin, and there is no hue bin at 360.
  Interval overlays MUST use the actual numeric bounds on the channel axis without snapping
  to whole bins; equal bounds MUST appear as a labeled line. Highlighted bins MUST NOT be
  presented as an exact count of selected pixels. At the supported minimum client area of
  960 by 640 pixels with 100% display scaling, charts, labels, interval markers, the toggle and
  six controls MUST remain visible without overlap or scrolling, with at least a 160 by 120
  pixel preview area for each of Original, Mask and Result.
- **FR-019**: The desktop workspace MUST use a restrained, consistent visual system with semantic
  roles for application background, work surfaces, primary action, text, muted text, borders,
  focus, disabled state and errors. Text and meaningful controls MUST meet a contrast ratio of
  at least 4.5:1 and 3:1 respectively in the delivered light theme.
- **FR-020**: The workspace MUST place HSV editing in a dedicated inspector beside the result
  workspace. Hue, saturation and value MUST each group their lower and upper controls, expose
  units and current values, and preserve the existing six-bound validation semantics.
- **FR-021**: The command area MUST prioritize opening media and progressively disclose actions
  by context. Playback and frame controls MUST appear only for video; output and experiment
  actions MUST remain visibly unavailable until a complete current result exists.
- **FR-022**: Original, Mask and Result MUST remain simultaneously available at the supported
  960 by 640 minimum client area, with each preview retaining a drawable area of at least
  160 by 120 pixels when the histogram is visible or hidden.
- **FR-023**: Keyboard traversal MUST follow the visible workflow, every interactive control
  MUST retain a visible focus indication, and opening image/video MUST have documented keyboard
  shortcuts that do not replace the visible controls.
- **FR-024**: Visual transitions MUST not delay input, move surrounding layout bounds, alter
  processing results, or ignore the user's reduced-motion preference. The desktop implementation
  MAY use immediate native state changes where animation would not improve comprehension.

### Key Entities *(include if feature involves data)*

- **Input Media**: A local image or video, its source identity, dimensions, and video frame
  position when relevant. The original input is preserved.
- **HSV Threshold Set**: Six named bounds with units and explicit hue wraparound semantics.
- **Segmentation Result**: A binary mask and extracted color image associated with exactly one
  source image or frame and one valid threshold set.
- **HSV Histogram**: Source/frame-associated frequency counts for H, S and V, plus the count
  omitted from hue due to low saturation. Counts are independent of segmentation thresholds.
- **Experiment Record**: An identified run linking source, thresholds, outputs, date, lighting
  conditions, and observations; accompanying experiment documentation identifies the environment.
- **Test Image Collection**: At least 10 distinct images with documented provenance and lighting
  coverage, used for repeatable demonstrations and threshold comparisons.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every valid file in the published supported-format demonstration set opens with
  a visible original and corresponding outputs; at least one video completes play, pause,
  threshold adjustment, and restart without a crash or mismatched views. The set MUST meet
  the minimum format coverage and inventory rules in Supported-Format Demonstration Set below;
  a skipped required codec case is unmet acceptance, not a passing result.
- **SC-002**: All pixels in known-color reference cases match their expected binary selections,
  including inclusive endpoints, equal bounds, hue wraparound, no selection, and full selection.
  Extracted pixels exactly match the expected retained or black colors.
- **SC-003**: On the documented demonstration computer, at least 95 of 100 valid threshold
  changes to a 1920 by 1080 still image show their updated outputs within one second after
  the final control change; after rapid changes, the final visible result always matches the
  final displayed thresholds.
- **SC-004**: Exported masks and results reopen at the source dimensions with identical mask
  values and extracted colors in every demonstration export case, including a video-frame export.
- **SC-005**: The demonstration produces at least 20 complete experiment records across at
  least 10 distinct images, with two threshold sets for each and at least two lighting conditions
  for one scene. A second student reproduces three selected runs with identical output pixels.
- **SC-006**: After reading the quick-start instructions, a student completes opening an image,
  adjusting thresholds, comparing all three views, and saving both outputs within five minutes
  without instructor intervention.
- **SC-007**: Every invalid-file, invalid-parameter, and failed-save acceptance case reports a
  message containing the applicable FR-013 fields without a crash, and the student can continue
  with a valid operation afterward. Cancellation preserves state and requires no error message.
- **SC-008**: The demonstration report includes labeled comparisons and observations about
  missed targets, unwanted selections, and lighting effects for all 10 test images.
- **SC-009**: For a known-color reference image, all 360 hue-bin counts (using S >= 5 percent),
  the excluded low-saturation count, and all 101 saturation/value-bin counts match hand-derived
  values. Moving valid bounds keeps these counts fixed and updates the interval overlays,
  including both pieces of a wrapped hue interval, while mask/result updates retain the original
  threshold semantics. Opening/closing the panel preserves synchronized result views. SC-003
  must still be met with the histogram panel visible. Equal-bound overlays and the minimum-size
  layout MUST meet US6 acceptance scenarios 6 and 7.
- **SC-010**: At both 960 by 640 and the documented large desktop size, automated layout checks
  and a manual walkthrough find zero overlapping labels or whole-window horizontal scrolling;
  all three previews retain at least 160 by 120 drawable pixels with the histogram shown and hidden.
- **SC-011**: In an empty, image and video session, 100 percent of controls in the acceptance
  inventory match their specified visible, hidden, enabled or disabled context state, without
  changing segmentation, export or playback results.
- **SC-012**: A keyboard-only walkthrough can open the image and video dialogs, reach all visible
  controls in workflow order, identify focus at every step, cancel safely, and return to the
  original application state without mouse input.

### Supported-Format Demonstration Set

Publish the acceptance inventory in `docs/acceptance.md` before final validation, with stable
case IDs, local paths or exact generation commands, SHA-256 file hashes, dimensions, source or
generation provenance, and expected opening/normalization outcomes. It MUST contain at least:

| Case ID | Required representation | Expected coverage |
| --- | --- | --- |
| FMT-001 | 8-bit RGB PNG | Color image opens with all three synchronized views |
| FMT-002 | 8-bit RGB JPEG | Decoded source displays and segments correctly |
| FMT-003 | 8-bit RGB BMP | Decoded source displays and segments correctly |
| FMT-004 | 8-bit grayscale PNG | Gray channels replicate into RGB |
| FMT-005 | 8-bit RGBA PNG | Stored RGB channels are used; alpha is ignored |
| FMT-006 | AVI containing MJPG video | First-frame opening and synchronized frame processing |
| FMT-007 | MP4 containing mp4v video | First-frame opening and synchronized frame processing |

For both video cases, record actual codec, frame count, frame dimensions, selected OpenCV
backend, and environment reference; at least one MUST exercise the complete SC-001 playback
sequence. Existing reproducible `tiny.avi`/`tiny.mp4` fixtures may supply the video cases, but
their generated bytes or exact generation procedure and actual hashes MUST be recorded.
Additional codecs are optional and their availability must be stated separately. These cases
may overlap the 10-image experiment collection, but format variants of the same image do not
count as distinct experiment images. Missing fixtures or unavailable required decoders remain
visible acceptance failures until resolved on the demonstration computer.

## Assumptions

- Primary users are students and instructors using local files on a university desktop or
  laptop. The initial demonstration targets Windows, matching the current project workspace;
  other desktop operating systems are not acceptance targets for this feature.
- Initial thresholds are H=(0,360), S=(0,100), V=(0,100), selecting the full HSV domain.
  Converted pixel hue is in [0,360); upper control value 360 is not normalized to zero.
  Thresholds persist when replacing the input within a session; automatic persistence between
  application launches is not required.
- Hue uses the user-facing degree scale and saturation/value use percentages. Conversion
  conventions and numerical precision are defined in contracts/processing.md; threshold comparisons
  use converted component values without rounding them to the control's integer step first.
- Grayscale input is treated as equal red, green, and blue channels. Transparent input uses
  its stored color channels with alpha ignored for segmentation and an opaque extracted output;
  this behavior must be explained in the user documentation.
- Video support means viewing and segmenting successive frames with play and pause. Seeking,
  audio playback, camera capture, full-video export, and guaranteed real-time playback rates
  are outside the initial scope. Play opens paused at the first frame; slower processing may
  reduce playback speed while maintaining synchronized views.
  Some video backends cannot distinguish exhaustion from acquisition failure. Such termination
  must stop safely with an ended-or-unreadable message and recovery guidance, retain the last
  valid frame, and allow restart; known fixture EOF and explicit decode errors remain tested.
- Segmentation quality evaluation is qualitative comparison with recorded observations.
  Ground-truth annotation tools, numerical accuracy scores, and automated lighting correction
  are outside the initial scope. Correct threshold membership is still verified quantitatively.
- Local experiment records and exported images provide comparison evidence; a separate
  experiment gallery or session database is not required. Students supply lighting descriptions
  and observations. No login, backend service, or database is needed.
- HSV histograms are descriptive aids only; the hue chart excludes pixels with S < 5 percent
  because hue is unstable near zero saturation, while S and V charts include all pixels. The
  5-percent cutoff is fixed and disclosed in the panel; charts never choose thresholds
  automatically. Histogram calculation uses the current decoded source/frame; its binning and
  hue display cutoff do not round HSV values or filter pixels for segmentation. Histogram image
  export, histogram persistence in experiment records, and automatic methods such as Otsu are
  outside this enhancement.
- Existing compatible GUI and utility components may be reused where available and suitably
  licensed, but reuse must not require running or installing the Image Restoration project.
  Planning found no reusable application modules in the current repository; any later supplied
  components must meet the same independence and licensing requirements.
- Object counting, tracking, machine learning, and additional segmentation algorithms are
  outside scope. The application must remain simple enough for student maintenance and explanation.
- The refreshed interface remains a light-first Windows desktop workspace. Dark mode, custom
  icon packages, decorative animation and a GUI-framework migration are outside this enhancement;
  native system typography and controls are preferred where they preserve the required hierarchy.
- Test images must be supplied or generated with documented provenance and usable permissions.
  Runtime measurements and reproducibility evidence depend on a documented demonstration
  computer, input collection, and software environment. Planning defines their recording format;
  implementation and validation must supply the actual inputs, versions, measurements and outcomes.
