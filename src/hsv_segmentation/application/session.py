"""Still-image session state independent of Tk widgets and dialogs."""

from pathlib import Path

import numpy as np

from ..errors import ValidationError
from ..io.images import load_image
from ..models import (
    AnalysisSettings,
    GrayscaleSettings,
    GroundTruth,
    HSVHistogram,
    HSVThresholdSet,
    InputMedia,
    MorphologySettings,
    OtsuOutcome,
    SegmentationMode,
    SegmentationResult,
    WatershedSettings,
)
from ..processing.color import rgb_to_hsv
from ..processing.histogram import compute_hsv_histogram
from ..processing.grayscale import (
    classify_grayscale, compute_otsu_threshold, extract_intensity, generate_grayscale_mask,
)
from ..processing.morphology import apply_morphology
from ..processing.object_analysis import analyze_components
from ..processing.evaluation import evaluate_masks
from ..processing.segmentation import apply_mask, generate_mask
from ..processing.watershed import separate_watershed
from ..processing.thresholds import validate_thresholds


def process_source(
    source: InputMedia,
    thresholds: HSVThresholdSet,
    request_revision: int,
    *,
    hsv=None,
    histogram: HSVHistogram | None = None,
    morphology: MorphologySettings | None = None,
    analysis_settings: AnalysisSettings | None = None,
    watershed_settings: WatershedSettings | None = None,
    ground_truth: GroundTruth | None = None,
    evaluation_target: str = "baseline",
    settings_revision: int = 0,
    segmentation_mode: SegmentationMode | str = SegmentationMode.HSV,
    grayscale_settings: GrayscaleSettings | None = None,
    threshold_ranges: tuple[HSVThresholdSet, ...] = (),
) -> SegmentationResult:
    """Create one immutable result for an already decoded source snapshot."""
    hsv_array = rgb_to_hsv(source.rgb) if hsv is None else hsv
    histogram = histogram or compute_hsv_histogram(hsv_array)
    morphology = morphology or MorphologySettings()
    analysis_settings = analysis_settings or AnalysisSettings()
    watershed_settings = watershed_settings or WatershedSettings()
    try:
        segmentation_mode = SegmentationMode(segmentation_mode)
    except (TypeError, ValueError) as error:
        raise ValidationError("segmentation_mode", "must be hsv or grayscale") from error
    grayscale_settings = grayscale_settings or GrayscaleSettings()
    if not isinstance(grayscale_settings, GrayscaleSettings):
        raise ValidationError("grayscale_settings", "must be GrayscaleSettings")
    eligibility = classify_grayscale(
        source.rgb, source.source_sha256, source.frame_index
    )
    otsu_outcome = OtsuOutcome()
    if segmentation_mode is SegmentationMode.GRAYSCALE:
        if not eligibility.eligible:
            raise ValidationError("segmentation_mode", eligibility.reason)
        intensity = extract_intensity(source.rgb)
        threshold = grayscale_settings.manual_threshold
        if grayscale_settings.threshold_source == "otsu":
            otsu_outcome = compute_otsu_threshold(
                intensity, source.source_sha256, source.frame_index
            )
            if otsu_outcome.status != "applied":
                raise ValidationError("otsu", otsu_outcome.reason)
            threshold = otsu_outcome.threshold
        original_mask = generate_grayscale_mask(
            intensity, threshold, grayscale_settings.polarity
        )
    else:
        ranges = threshold_ranges or (thresholds,)
        original_mask = generate_mask(hsv_array, ranges[0])
        for color_range in ranges[1:]:
            original_mask = np.maximum(
                original_mask, generate_mask(hsv_array, color_range)
            )
    mask = apply_morphology(original_mask, morphology)
    segmented_rgb = apply_mask(source.rgb, mask)
    analysis = (
        analyze_components(mask, analysis_settings)
        if analysis_settings.enabled else None
    )
    watershed = (
        separate_watershed(source.rgb, mask, watershed_settings, analysis_settings.min_area_px)
        if watershed_settings.enabled else None
    )
    prediction = None
    if evaluation_target == "baseline":
        prediction = mask
    elif evaluation_target == "components" and analysis is not None:
        prediction = analysis.filtered_mask
    elif (
        evaluation_target == "watershed" and watershed is not None
        and watershed.status in {"applied", "empty"}
    ):
        prediction = watershed.foreground_mask
    evaluation = (
        evaluate_masks(prediction, ground_truth.mask, target=evaluation_target)
        if ground_truth is not None and prediction is not None else None
    )
    return SegmentationResult(
        source=source,
        thresholds=thresholds,
        mask=mask,
        segmented_rgb=segmented_rgb,
        request_revision=request_revision,
        histogram=histogram,
        morphology=morphology,
        original_mask=original_mask,
        analysis_settings=analysis_settings,
        watershed_settings=watershed_settings,
        analysis=analysis,
        watershed=watershed,
        ground_truth=ground_truth,
        evaluation_target=evaluation_target,
        evaluation=evaluation,
        settings_revision=settings_revision,
        segmentation_mode=segmentation_mode,
        grayscale_settings=grayscale_settings,
        grayscale_eligibility=eligibility,
        otsu_outcome=otsu_outcome,
        threshold_ranges=threshold_ranges,
    )


class ImageSession:
    """Own the last successfully committed source, thresholds and result."""

    def __init__(
        self,
        thresholds: HSVThresholdSet | None = None,
        morphology: MorphologySettings | None = None,
        analysis_settings: AnalysisSettings | None = None,
        watershed_settings: WatershedSettings | None = None,
    ):
        self._thresholds = thresholds or HSVThresholdSet()
        self._threshold_ranges: tuple[HSVThresholdSet, ...] = ()
        self._morphology = morphology or MorphologySettings()
        self._analysis_settings = analysis_settings or AnalysisSettings()
        self._watershed_settings = watershed_settings or WatershedSettings()
        self._ground_truth: GroundTruth | None = None
        self._evaluation_target = "baseline"
        self._settings_revision = 0
        self._segmentation_mode = SegmentationMode.HSV
        self._grayscale_settings = GrayscaleSettings()
        self._source: InputMedia | None = None
        self._result: SegmentationResult | None = None
        self._request_revision = 0

    @property
    def thresholds(self) -> HSVThresholdSet:
        return self._thresholds

    @property
    def threshold_ranges(self) -> tuple[HSVThresholdSet, ...]:
        return self._threshold_ranges

    @property
    def source(self) -> InputMedia | None:
        return self._source

    @property
    def morphology(self) -> MorphologySettings:
        return self._morphology

    @property
    def analysis_settings(self) -> AnalysisSettings:
        return self._analysis_settings

    @property
    def watershed_settings(self) -> WatershedSettings:
        return self._watershed_settings

    @property
    def ground_truth(self) -> GroundTruth | None:
        return self._ground_truth

    @property
    def evaluation_target(self) -> str:
        return self._evaluation_target

    @property
    def settings_revision(self) -> int:
        return self._settings_revision

    @property
    def segmentation_mode(self) -> SegmentationMode:
        return self._segmentation_mode

    @property
    def grayscale_settings(self) -> GrayscaleSettings:
        return self._grayscale_settings

    def accept_segmentation_mode(self, mode: SegmentationMode | str) -> None:
        try:
            selected = SegmentationMode(mode)
        except (TypeError, ValueError) as error:
            raise ValidationError("segmentation_mode", "must be hsv or grayscale") from error
        if selected is SegmentationMode.GRAYSCALE:
            if self._source is None:
                raise ValidationError("segmentation_mode", "requires a current source")
            eligibility = classify_grayscale(
                self._source.rgb, self._source.source_sha256, self._source.frame_index
            )
            if not eligibility.eligible:
                raise ValidationError("segmentation_mode", eligibility.reason)
        self._segmentation_mode = selected
        self._settings_revision += 1

    def accept_grayscale_settings(self, settings: GrayscaleSettings) -> None:
        if not isinstance(settings, GrayscaleSettings):
            raise ValidationError("grayscale_settings", "must be GrayscaleSettings")
        self._grayscale_settings = settings
        self._settings_revision += 1

    def restore_processing_selection(self, result: SegmentationResult) -> None:
        """Restore the last committed mode/settings after a recoverable candidate fails."""
        if result is not self._result:
            raise ValidationError("result", "must be the current committed result")
        self._segmentation_mode = result.segmentation_mode
        self._grayscale_settings = result.grayscale_settings
        self._settings_revision = result.settings_revision

    @property
    def result(self) -> SegmentationResult | None:
        return self._result

    @property
    def request_revision(self) -> int:
        return self._request_revision

    def preserved_state_description(self) -> str:
        """Describe the committed state retained after a candidate operation fails."""
        if self._result is None:
            return "No prior input or result existed; valid thresholds were preserved."
        if self._source is not None and self._source.media_kind == "video":
            return "The last valid video frame, thresholds, and result were preserved."
        return "The previous valid input, thresholds, and result were preserved."

    def open_image(self, path: str | Path | None) -> SegmentationResult | None:
        """Decode/process a candidate fully, then atomically commit it.

        ``None`` represents a cancelled file dialog and leaves all state intact.
        Any decoding or processing exception likewise occurs before commit.
        """
        if path is None or str(path) == "":
            return self._result
        candidate = load_image(path)
        next_revision = self._request_revision + 1
        candidate_result = process_source(
            candidate, self._thresholds, next_revision, morphology=self._morphology,
            analysis_settings=self._analysis_settings,
            watershed_settings=self._watershed_settings,
            evaluation_target=self._evaluation_target,
            settings_revision=self._settings_revision,
            segmentation_mode=SegmentationMode.HSV,
            grayscale_settings=self._grayscale_settings,
            threshold_ranges=self._threshold_ranges,
        )
        self._source = candidate
        self._segmentation_mode = SegmentationMode.HSV
        self._result = candidate_result
        self._request_revision = next_revision
        return candidate_result

    def set_thresholds(self, thresholds: HSVThresholdSet) -> SegmentationResult | None:
        """Accept a valid set and synchronously reprocess the current still image."""
        validated = validate_thresholds(thresholds)
        next_revision = self._request_revision + 1
        candidate_result = (
            process_source(
                self._source, validated, next_revision, morphology=self._morphology,
                analysis_settings=self._analysis_settings,
                watershed_settings=self._watershed_settings,
                ground_truth=self._ground_truth,
                evaluation_target=self._evaluation_target,
                settings_revision=self._settings_revision,
                segmentation_mode=self._segmentation_mode,
                grayscale_settings=self._grayscale_settings,
                threshold_ranges=(),
            )
            if self._source is not None else None
        )
        self._thresholds = validated
        self._threshold_ranges = ()
        self._result = candidate_result
        self._request_revision = next_revision
        return candidate_result

    def accept_thresholds(self, thresholds: HSVThresholdSet) -> None:
        """Accept controls immediately while leaving the old result pending."""
        self._thresholds = validate_thresholds(thresholds)
        self._threshold_ranges = ()

    def accept_threshold_ranges(
        self, ranges: tuple[HSVThresholdSet, ...]
    ) -> None:
        """Accept two to four independent color ranges for OR segmentation."""
        if not isinstance(ranges, tuple) or not 2 <= len(ranges) <= 4:
            raise ValidationError("threshold_ranges", "must contain 2..4 HSV ranges")
        validated = tuple(validate_thresholds(item) for item in ranges)
        self._thresholds = validated[0]
        self._threshold_ranges = validated

    def accept_morphology(self, morphology: MorphologySettings) -> None:
        if not isinstance(morphology, MorphologySettings):
            raise ValidationError("morphology", "must be MorphologySettings")
        self._morphology = morphology

    def accept_analysis(self, settings: AnalysisSettings) -> None:
        if not isinstance(settings, AnalysisSettings):
            raise ValidationError("analysis", "must be AnalysisSettings")
        self._analysis_settings = settings
        self._settings_revision += 1

    def accept_watershed(self, settings: WatershedSettings) -> None:
        if not isinstance(settings, WatershedSettings):
            raise ValidationError("watershed", "must be WatershedSettings")
        self._watershed_settings = settings
        self._settings_revision += 1

    def bind_ground_truth(self, truth: GroundTruth | None) -> None:
        if truth is not None:
            if self._source is None:
                raise ValidationError("ground_truth", "requires a current source")
            identity = (truth.session_id, truth.source_image_sha256, truth.frame_index)
            current = (self._source.session_id, self._source.source_sha256, self._source.frame_index)
            if identity != current:
                raise ValidationError("ground_truth", "must be bound to the current source/frame")
        self._ground_truth = truth
        self._settings_revision += 1

    def set_evaluation_target(self, target: str) -> None:
        if target not in {"baseline", "components", "watershed"}:
            raise ValidationError("evaluation_target", "is invalid")
        self._evaluation_target = target
        self._settings_revision += 1

    def commit_candidate(self, result: SegmentationResult) -> None:
        """Commit a fully decoded and processed replacement image."""
        self._source = result.source
        self._thresholds = result.thresholds
        self._threshold_ranges = result.threshold_ranges
        self._morphology = result.morphology
        self._analysis_settings = result.analysis_settings
        self._watershed_settings = result.watershed_settings
        self._ground_truth = result.ground_truth
        self._evaluation_target = result.evaluation_target
        self._settings_revision = result.settings_revision
        self._segmentation_mode = result.segmentation_mode
        self._grayscale_settings = result.grayscale_settings
        self._result = result
        self._request_revision = max(self._request_revision, result.request_revision)

    def commit_result(self, result: SegmentationResult) -> bool:
        """Commit only a result for the current source and threshold revision."""
        if self._source is None or result.session_id != self._source.session_id:
            return False
        if not self._matches_current_settings(result):
            return False
        if result.request_revision < self._request_revision:
            return False
        self._result = result
        self._request_revision = result.request_revision
        return True

    def commit_frame_result(self, result: SegmentationResult) -> bool:
        """Advance the current video session to a synchronized processed frame."""
        if self._source is None or self._source.media_kind != "video":
            return False
        if result.session_id != self._source.session_id:
            return False
        if not self._matches_current_settings(result):
            return False
        if result.request_revision < self._request_revision:
            return False
        if result.frame_index is None:
            return False
        self._source = result.source
        self._ground_truth = None
        self._result = result
        self._request_revision = result.request_revision
        return True

    def _matches_current_settings(self, result: SegmentationResult) -> bool:
        """Return whether a completion belongs to the active processing configuration."""
        return (
            result.parameter_revision == self._thresholds.parameter_revision
            and result.threshold_ranges == self._threshold_ranges
            and result.morphology == self._morphology
            and result.analysis_settings == self._analysis_settings
            and result.watershed_settings == self._watershed_settings
            and result.settings_revision == self._settings_revision
            and result.segmentation_mode == self._segmentation_mode
            and result.grayscale_settings == self._grayscale_settings
        )
