"""Still-image session state independent of Tk widgets and dialogs."""

from pathlib import Path

from ..io.images import load_image
from ..models import HSVHistogram, HSVThresholdSet, InputMedia, SegmentationResult
from ..processing.color import rgb_to_hsv
from ..processing.histogram import compute_hsv_histogram
from ..processing.segmentation import apply_mask, generate_mask
from ..processing.thresholds import validate_thresholds


def process_source(
    source: InputMedia,
    thresholds: HSVThresholdSet,
    request_revision: int,
    *,
    hsv=None,
    histogram: HSVHistogram | None = None,
) -> SegmentationResult:
    """Create one immutable result for an already decoded source snapshot."""
    hsv_array = rgb_to_hsv(source.rgb) if hsv is None else hsv
    histogram = histogram or compute_hsv_histogram(hsv_array)
    mask = generate_mask(hsv_array, thresholds)
    segmented_rgb = apply_mask(source.rgb, mask)
    return SegmentationResult(
        source=source,
        thresholds=thresholds,
        mask=mask,
        segmented_rgb=segmented_rgb,
        request_revision=request_revision,
        histogram=histogram,
    )


class ImageSession:
    """Own the last successfully committed source, thresholds and result."""

    def __init__(self, thresholds: HSVThresholdSet | None = None):
        self._thresholds = thresholds or HSVThresholdSet()
        self._source: InputMedia | None = None
        self._result: SegmentationResult | None = None
        self._request_revision = 0

    @property
    def thresholds(self) -> HSVThresholdSet:
        return self._thresholds

    @property
    def source(self) -> InputMedia | None:
        return self._source

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
        candidate_result = process_source(candidate, self._thresholds, next_revision)
        self._source = candidate
        self._result = candidate_result
        self._request_revision = next_revision
        return candidate_result

    def set_thresholds(self, thresholds: HSVThresholdSet) -> SegmentationResult | None:
        """Accept a valid set and synchronously reprocess the current still image."""
        validated = validate_thresholds(thresholds)
        next_revision = self._request_revision + 1
        candidate_result = (
            process_source(self._source, validated, next_revision)
            if self._source is not None else None
        )
        self._thresholds = validated
        self._result = candidate_result
        self._request_revision = next_revision
        return candidate_result

    def accept_thresholds(self, thresholds: HSVThresholdSet) -> None:
        """Accept controls immediately while leaving the old result pending."""
        self._thresholds = validate_thresholds(thresholds)

    def commit_candidate(self, result: SegmentationResult) -> None:
        """Commit a fully decoded and processed replacement image."""
        self._source = result.source
        self._thresholds = result.thresholds
        self._result = result
        self._request_revision = max(self._request_revision, result.request_revision)

    def commit_result(self, result: SegmentationResult) -> bool:
        """Commit only a result for the current source and threshold revision."""
        if self._source is None or result.session_id != self._source.session_id:
            return False
        if result.parameter_revision != self._thresholds.parameter_revision:
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
        if result.parameter_revision != self._thresholds.parameter_revision:
            return False
        if result.request_revision < self._request_revision:
            return False
        if result.frame_index is None:
            return False
        self._source = result.source
        self._result = result
        self._request_revision = result.request_revision
        return True
