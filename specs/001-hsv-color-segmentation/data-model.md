# Data Model: HSV Color Segmentation

**Status**: Design contract; implementation pending. Units and field names are authoritative
for tasks and local records. No database is required.

## InputMedia

| Field | Type / constraint |
| --- | --- |
| session_id | Unique string; changes only when a candidate source is successfully committed |
| source_path | Absolute local path at runtime; portable records use a relative path when possible |
| source_sha256 | SHA-256 of original source bytes for reproducibility; computed outside GUI thread |
| media_kind | image or video |
| width, height | Positive integers; width*height <=12,000,000 |
| source_format | Actual recognized format; image PNG/JPEG/BMP or decodable MP4/AVI container |
| rgb | Nonempty uint8 RGB array with shape (height,width,3); no alpha |
| frame_index | Zero-based decoded frame position for video; null for still images |
| backend | Decoder/backend description for video; null for images |

Grayscale channels replicate into RGB. PNG alpha is ignored, not composited. Accept standard
8-bit L, LA, RGB, RGBA and palette images (including palette transparency) after documented
RGB conversion. Reject unsupported high-bit-depth/float/CMYK modes with an actionable message.
Do not silently rescale unsupported data into the core input contract. Apply pixel-limit and
Pillow safeguard checks, decode completely, and close image handles before session commit.
Raster orientation is the stored decoded orientation; do not silently apply EXIF transforms.
No source file is changed. A video capture handle is owned by the I/O adapter, not persisted
in experiment records or exposed as a GUI object.

## HSVThresholdSet

| Field | Type / constraint |
| --- | --- |
| lower_h_deg | Integer; 0 <= lower_h_deg <=359 |
| upper_h_deg | Integer; 0 <= upper_h_deg <=360; 360 is upper endpoint only |
| lower_s_pct, upper_s_pct | Integers; 0 <= lower_s_pct <= upper_s_pct <=100 |
| lower_v_pct, upper_v_pct | Integers; 0 <= lower_v_pct <= upper_v_pct <=100 |
| parameter_revision | Nonnegative integer incremented for each accepted changed set |

Reject booleans as numeric bounds, fractional values, nonfinite values and malformed text.
GUI text parsing is separate from pure typed validation. An incomplete/invalid edit does not
replace the last valid threshold set; show pending/invalid state and disable export while the
visible controls do not describe the displayed snapshot. No implicit clamping or swapping.
Default bounds: (0,360,0,100,0,100). Ordered hue uses a closed interval; reversed hue wraps through
zero. Equal hue bounds below 360 select only that exact hue, not all hues. Upper 360 is never
normalized to zero when storing or comparing the interval.

## HSVImage

Float64 array with shape (height,width,3), finite H in [0,360), S/V in [0,100]. This is a derived
in-memory value, not an independent persisted image. Achromatic colors use H=0 and S=0; black
has V=0. Conversion retains fractional components. Never reinterpret an OpenCV uint8 HSV array
as this representation. Cache at most the active source/frame's conversion; clear on replacement.

## SegmentationResult

| Field | Type / constraint |
| --- | --- |
| session_id, parameter_revision | Exactly identify the accepted request |
| frame_index | Matches the associated source/frame; null for still images |
| thresholds | Complete immutable copy of the six valid values |
| original_rgb | RGB data for the displayed source/frame |
| mask | uint8 (height,width), values only 0 or 255 |
| segmented_rgb | uint8 (height,width,3); original RGB where selected, zeros elsewhere |
| width, height | Same dimensions as original_rgb |

Use explicit ownership: do not mutate arrays after handing a result to the GUI. A new edit
invalidates export eligibility until an accepted new result is displayed. Video advancing to
a new frame does not permit an export to mix an older mask with newer RGB. Export captures
the entire displayed immutable result and writes it independently of subsequent playback.
Preview scaling must not change any source-resolution field.

## ProcessingRequest and SessionState

A request contains session_id, monotonically increasing request_revision, parameter_revision,
frame_index, RGB data and the valid threshold set. The worker processes one request at a time;
one newer pending request replaces older pending work. Completion messages contain plain data
or typed errors. GUI presentation accepts only results matching the current session and current
parameter revision, and never moves backward in frame/request revision. A new video frame is
scheduled only after accepting/handling the current one so playback does not starve rendering.

States: Empty -> LoadingCandidate -> ReadyImage or ReadyVideoPaused. During candidate loading,
keep the previous committed session. Failed/cancelled loads return to that session unchanged.
ReadyVideoPaused -> Playing -> Paused or Ended; restart reopens and decodes frame zero.
Processing is an orthogonal pending flag; incomplete or invalid controls disable export.
Explicit decode failure stops playback and retains the last valid result with an error status.
Unknown termination stops with an honest ended-or-unreadable message, never a false diagnosis.
Shutdown rejects new work, releases captures, discards stale callbacks and closes the window
without an indefinite join in the Tk event thread.

## ExperimentRecord

| Field | Type / constraint |
| --- | --- |
| schema_version | Integer 1 for the initial local record format |
| run_id | Unique UUID string; used for an exclusive new run directory |
| created_at | ISO-8601 UTC timestamp |
| source | Media identity/path/hash, dimensions and optional frame index/backend |
| thresholds | Exactly six named integer bounds with degrees/percent units as above |
| lighting | Nonempty user description; no claim of measured illumination unless supplied |
| observations | Nonempty qualitative note about missed targets/unwanted selection/quality |
| artifacts | Relative mask/result PNG paths with SHA-256 file hashes and decoded-pixel hashes |
| environment | Relative environment-record path and its SHA-256 |

Record paths resolve relative to the record directory. Source paths may point outside it, but
source hashes must be checked before replay. Pixel hashes include array shape, dtype/channel
order and contiguous decoded bytes so comparisons do not depend on PNG metadata. Environment
records contain OS/CPU/RAM, interpreter/Tcl/Tk, exact package/build-tool versions, application
revision and decoder backend. A video replay also requires the same decoder environment.
Publish the complete record only after both PNGs and metadata dependencies succeed. Failed
publication leaves no record that advertises completeness; report orphan outputs for retry.
General user-selected standalone exports still require overwrite confirmation.

## TestImageCollection and AcceptanceEvidence

`experiments/manifest.json` identifies at least 10 distinct images, their hashes/provenance,
permissions, scene identifiers and lighting descriptions. One photographed scene has two real
lighting conditions; generated images are labeled separately. Each image links to two threshold
runs. Records and images remain local and reusable by a second student.

Acceptance evidence distinguishes automatic reproduction of three runs from independent
student reproduction and the timed five-minute workflow. Record participant/date/outcome and
observed issues; keep unavailable evidence pending. Documentation can be prepared before these
human checks, but final academic acceptance cannot be declared complete without them.
