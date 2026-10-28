"""Exact binary overlap counts and segmentation similarity scores."""

import numpy as np

from ..errors import ValidationError
from ..models import EvaluationResult


def _validate(mask: np.ndarray, name: str) -> None:
    if (
        not isinstance(mask, np.ndarray) or mask.dtype != np.uint8 or mask.ndim != 2
        or min(mask.shape, default=0) == 0
        or not np.all((mask == 0) | (mask == 255))
    ):
        raise ValidationError(name, "must be a nonempty binary uint8 array")


def evaluate_masks(
    prediction: np.ndarray, truth: np.ndarray, *, target: str = "baseline"
) -> EvaluationResult:
    _validate(prediction, "prediction")
    _validate(truth, "truth")
    if prediction.shape != truth.shape:
        raise ValidationError("truth", "dimensions must match prediction")
    predicted = prediction == 255
    expected = truth == 255
    tp = int(np.count_nonzero(predicted & expected))
    fp = int(np.count_nonzero(predicted & ~expected))
    fn = int(np.count_nonzero(~predicted & expected))
    tn = int(prediction.size - tp - fp - fn)
    union = tp + fp + fn
    total_foreground = 2 * tp + fp + fn
    if union == 0:
        iou = dice = 1.0
        status = "both_empty"
    elif tp == 0 and (fp == 0 or fn == 0):
        iou = dice = 0.0
        status = "one_empty"
    else:
        iou = tp / union
        dice = 2 * tp / total_foreground
        status = "normal"
    return EvaluationResult(target, tp, fp, fn, tn, iou, dice, status)
