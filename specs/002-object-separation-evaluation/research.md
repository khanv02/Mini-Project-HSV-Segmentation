# Research and Repository Inspection

Date: 2026-10-28. Scope: tracked project structure, runtime source/imports, tests, packaging,
scripts, existing SDD, algorithm/acceptance/verification docs and experiment publication.
Generated datasets, virtual environments and tool caches are evidence/dependencies, not code
to redesign. No source changes or evidence regeneration were performed during planning.

## Verified inventory

| Concern | Existing implementation | Reuse decision |
| --- | --- | --- |
| Package | `src/hsv_segmentation`, `pyproject.toml`, `uv.lock`, requirements manifests | Keep one package and current entrypoints |
| GUI | `gui/main_window.py`, `controller.py`, `image_view.py`, `theme.py`; Tkinter/ttk and Pillow ImageTk | Extend current widgets and controller; no toolkit migration |
| HSV | `processing/color.py:rgb_to_hsv`, `segmentation.py:generate_mask/apply_mask/segment`, `thresholds.py` | Preserve float64 degrees/percentages, inclusive bounds and hue wraparound |
| Morphology | `processing/morphology.py:apply_morphology`; `models.py:MorphologySettings`; `gui/morphology_controls.py` | Reuse optional opening/closing/opening_closing, odd kernels 3/5/7/9 |
| Sampling | `processing/threshold_suggestions.py:sample_color/sample_color_region/suggest_thresholds`, `HSV_PRESETS`; ROI mapping in `gui/image_view.py` | Keep sampling against original pixels, including annotated previews |
| Histogram | `processing/histogram.py:compute_hsv_histogram`, `gui/hsv_histogram.py:HSVHistogramPanel` | Keep source counts/cache and 5% hue-display cutoff |
| Models | `models.py:InputMedia/ProcessingRequest/SegmentationResult` | Immutable snapshots; append optional fields without shifting existing positional arguments |
| State | `application/session.py:ImageSession/process_source` | Add settings/truth state and commit guards here |
| Worker | `application/processing_worker.py:ProcessingWorker/_CachedProcessor` | One serialized worker, coalesced replaceable work, required writes; no Tk access from worker |
| Video | `application/playback.py:PlaybackSession`, `io/video.py:VideoReader` | Thread settings through open/next/reprocess/restart, retain decoding limits |
| Export | `io/export.py:export_snapshot/save_mask_png/save_result_png` | Preserve baseline mask/result PNG semantics |
| Experiments | `io/experiments.py:publish_experiment/pixel_sha256/_write_record` | UUID directory, artifact-first publication, atomic record replace, hashes |
| Errors | `errors.py:ValidationError/InputError/DecodeError/WriteError/format_recovery_message` | Extend cause/action coverage rather than introduce a parallel error system |
| Tests | `tests/unit`, `tests/integration`, `tests/fixtures/color_cases.py` | Extend analytical fixtures, Tk polling/delayed worker tests and replay tests |
| Tooling | `scripts/generate_acceptance_media.py`, `generate_experiment_evidence.py`, `benchmark_gui_performance.py` | Reuse patterns; do not overwrite retained baseline evidence |
| Documentation | `README.md`, `docs/{algorithm,acceptance,verification,implementation-stages}.md`, `experiments/` | Add clearly separate extension evidence during implementation |

Dependencies verified from pyproject: Python >=3.11, NumPy >=2,<3, Pillow >=11,<13,
opencv-python >=4,<5; pytest >=8,<10 optional test extra. Local interpreter currently resolves
to Python 3.14 and OpenCV 4.14.0; this is inspection context, not a claim of Python 3.11 testing.
Prior verification records 248 passing tests and independent human acceptance still pending.
No tests were executed by this planning workflow; do not promote historical results to new evidence.

## Decisions

1. **Keep the architecture.** Add three pure algorithm modules and one truth I/O adapter;
   integrate through existing models/application/controller. Reject rewriting the pipeline,
   adding services, SciPy/scikit-image or a plugin framework: current NumPy/OpenCV suffice.
2. **Analyze the current baseline.** Baseline means exact HSV mask after existing optional
   morphology. Preserve raw HSV in `original_mask`. Filtering creates a separate prediction;
   polygon contours annotate regions but never define pixel area.
3. **Separate labels from foreground union.** Watershed may split labels without materially
   improving binary overlap. Exclude ridge pixels explicitly and never advertise IoU as an
   instance-separation score. No guarantee of separation for arbitrary input.
4. **Explicit seed construction.** Distance threshold produces seed components, not universal
   local-maximum detection. Require >=2 foreground seed labels and usable background; otherwise
   report not-applied. This modest deterministic design meets the reference fixture without
   inventing robustness or marker-editing scope.
5. **Truth rules.** Lossless grayscale-equivalent PNG/BMP only, strict > threshold, alpha
   ignored with disclosure, no resizing. Reject colored annotations and 16-bit/float formats
   rather than silently guess class colors or scale.
6. **Truth belongs to a frame.** Pause before loading, include binding and truth revision in
   requests, clear on frame/source changes/restart. Retain truth during threshold/analysis edits.
7. **Version records conservatively.** Disabled extensions preserve schema 1 behavior. Extended
   runs use schema 2 retaining baseline keys; project replay dispatches by version. Unknown
   versions fail clearly. Existing schema-1 files are never rewritten; external consumers of
   schema 2 need explicit support.

## API verification

Inspected installed OpenCV docstrings for `connectedComponentsWithStats`, `findContours`,
`watershed` and `distanceTransform`. The first accepts 8-bit masks, connectivity 4/8 and int32
labels; statistics include background. Watershed accepts 8-bit 3-channel source and mutates
int32 markers with -1 ridges. Use copies at that boundary. New Python module/function names
in contracts are proposed additions, not claimed existing APIs.

No extension registry `.specify/extensions.yml` was present; pre/post hooks for constitution,
specification, planning and tasks therefore do not apply. No unresolved design clarification.
