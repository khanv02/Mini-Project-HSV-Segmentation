"""Pure display-only compositions derived from validated segmentation data."""

from numbers import Real

import numpy as np

from ..errors import ValidationError
from ..models import validate_rgb
from ..models import RegionAnalysis, WatershedResult


def compose_segmentation_overlay(
    rgb: np.ndarray,
    mask: np.ndarray,
    *,
    color: tuple[int, int, int] = (0, 255, 80),
    opacity: float = 0.35,
) -> np.ndarray:
    """Tint selected pixels while retaining the complete original image."""
    height, width = validate_rgb(rgb)
    if (
        not isinstance(mask, np.ndarray)
        or mask.dtype != np.uint8
        or mask.shape != (height, width)
        or not np.all((mask == 0) | (mask == 255))
    ):
        raise ValidationError("mask", "must be a source-sized binary uint8 array")
    if (
        not isinstance(color, tuple)
        or len(color) != 3
        or any(isinstance(channel, bool) or not isinstance(channel, int) or not 0 <= channel <= 255
               for channel in color)
    ):
        raise ValidationError("color", "must contain three integer channels in 0..255")
    if isinstance(opacity, bool) or not isinstance(opacity, Real) or not 0.0 <= opacity <= 1.0:
        raise ValidationError("opacity", "must be a number in 0..1")

    overlay = rgb.copy()
    selected = mask == 255
    tint = np.asarray(color, dtype=np.float64)
    blended = np.rint(
        rgb[selected].astype(np.float64) * (1.0 - float(opacity))
        + tint * float(opacity)
    )
    overlay[selected] = blended.astype(np.uint8)
    return overlay


def compose_region_annotations(
    rgb: np.ndarray, analysis: RegionAnalysis, *, contours: bool = True,
    boxes: bool = True, color: tuple[int, int, int] = (255, 64, 64),
) -> np.ndarray:
    """Draw source-coordinate component contours and boxes on an owned RGB copy."""
    import cv2

    shape = validate_rgb(rgb)
    if not isinstance(analysis, RegionAnalysis) or analysis.labels.shape != shape:
        raise ValidationError("analysis", "must match RGB dimensions")
    output = rgb.copy()
    draw_color = tuple(int(channel) for channel in color)
    for region in analysis.regions:
        if contours:
            cv2.drawContours(output, list(region.contours), -1, draw_color, 1)
        if boxes:
            x, y, width, height = region.box
            cv2.rectangle(output, (x, y), (x + width - 1, y + height - 1), draw_color, 1)
    return output


def compose_confusion_overlay(
    rgb: np.ndarray, prediction: np.ndarray, truth: np.ndarray,
) -> np.ndarray:
    """Color TP green, FP red and FN blue while retaining true-negative source pixels."""
    validate_rgb(rgb)
    shape = rgb.shape[:2]
    for name, mask in (("prediction", prediction), ("truth", truth)):
        if (
            not isinstance(mask, np.ndarray) or mask.dtype != np.uint8 or mask.shape != shape
            or not np.all((mask == 0) | (mask == 255))
        ):
            raise ValidationError(name, "must be a source-sized binary uint8 mask")
    output = rgb.copy()
    p, t = prediction == 255, truth == 255
    output[p & t] = (40, 190, 80)
    output[p & ~t] = (230, 70, 70)
    output[~p & t] = (60, 120, 240)
    return output


def compose_watershed_overlay(
    rgb: np.ndarray, result: WatershedResult,
) -> np.ndarray:
    """Tint separated labels and draw watershed ridges on an owned RGB copy."""
    shape = validate_rgb(rgb)
    if not isinstance(result, WatershedResult) or result.labels.shape != shape:
        raise ValidationError("watershed", "must match RGB dimensions")

    output = rgb.copy()
    palette = np.asarray(
        ((47, 158, 255), (255, 166, 47), (132, 204, 22), (168, 85, 247),
         (236, 72, 153), (20, 184, 166)),
        dtype=np.float64,
    )
    for label in np.unique(result.labels):
        if label <= 0:
            continue
        selected = result.labels == label
        tint = palette[(int(label) - 1) % len(palette)]
        output[selected] = np.rint(
            rgb[selected].astype(np.float64) * 0.55 + tint * 0.45
        ).astype(np.uint8)
    output[result.boundaries == 255] = (255, 32, 32)
    return output

