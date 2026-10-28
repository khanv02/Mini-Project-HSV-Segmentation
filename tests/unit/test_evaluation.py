import numpy as np
import pytest

from hsv_segmentation.errors import ValidationError
from hsv_segmentation.processing.evaluation import evaluate_masks
from tests.fixtures.analysis_cases import partial_overlap_masks


def test_partial_overlap_has_exact_counts_and_scores() -> None:
    prediction, truth = partial_overlap_masks()
    result = evaluate_masks(prediction, truth)
    assert (result.true_positive, result.false_positive, result.false_negative, result.true_negative) == (2, 1, 1, 0)
    assert result.iou == pytest.approx(0.5, abs=1e-12)
    assert result.dice == pytest.approx(2 / 3, abs=1e-12)


def test_empty_disjoint_and_identical_cases() -> None:
    empty = np.zeros((3, 3), np.uint8); full = np.full((3, 3), 255, np.uint8)
    both = evaluate_masks(empty, empty)
    assert (both.iou, both.dice, both.status) == (1.0, 1.0, "both_empty")
    one = evaluate_masks(empty, full)
    assert (one.iou, one.dice, one.status) == (0.0, 0.0, "one_empty")
    left = np.array([[255, 0]], np.uint8); right = np.array([[0, 255]], np.uint8)
    assert evaluate_masks(left, right).iou == 0
    assert evaluate_masks(left, left).dice == 1


def test_rejects_mismatch_and_nonbinary() -> None:
    with pytest.raises(ValidationError, match="dimensions"):
        evaluate_masks(np.zeros((2, 2), np.uint8), np.zeros((3, 2), np.uint8))
    with pytest.raises(ValidationError, match="binary"):
        evaluate_masks(np.array([[1]], np.uint8), np.zeros((1, 1), np.uint8))
