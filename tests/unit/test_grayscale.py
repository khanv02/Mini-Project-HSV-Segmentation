"""Analytical tests for exact grayscale segmentation and global Otsu."""

import numpy as np
import pytest

from hsv_segmentation.errors import ValidationError
from hsv_segmentation.processing.grayscale import (
    classify_grayscale,
    compute_otsu_threshold,
    extract_intensity,
    generate_grayscale_mask,
)


def test_exact_eligibility_and_owned_intensity(exact_gray_rgb, nearly_gray_rgb):
    yes = classify_grayscale(exact_gray_rgb, "a" * 64)
    no = classify_grayscale(nearly_gray_rgb, "a" * 64)
    assert yes.eligible and yes.reason is None
    assert not no.eligible and "equal" in no.reason
    intensity = extract_intensity(exact_gray_rgb)
    exact_gray_rgb.fill(255)
    assert intensity[0, 0] == 0


@pytest.mark.parametrize("threshold", [0, 64, 128, 255])
def test_manual_polarities_are_exact_complements(exact_gray_rgb, threshold):
    intensity = extract_intensity(exact_gray_rgb)
    bright = generate_grayscale_mask(intensity, threshold, "bright")
    dark = generate_grayscale_mask(intensity, threshold, "dark")
    assert np.array_equal(bright == 255, intensity > threshold)
    assert np.array_equal(dark == 255, intensity <= threshold)
    assert np.array_equal(bright, 255 - dark)


@pytest.mark.parametrize("bad", [True, -1, 256, 1.5, "4"])
def test_manual_threshold_rejects_invalid_values(exact_gray_rgb, bad):
    with pytest.raises(ValidationError):
        generate_grayscale_mask(extract_intensity(exact_gray_rgb), bad, "bright")


def test_otsu_uses_smallest_optimal_threshold(two_level_gray_rgb):
    intensity = extract_intensity(two_level_gray_rgb)
    outcome = compute_otsu_threshold(intensity, "b" * 64)
    assert outcome.status == "applied"
    assert outcome.threshold == 20
    assert outcome.tie_rule == "smallest_optimal_threshold"


def test_otsu_constant_is_explicitly_unavailable(constant_gray_rgb):
    outcome = compute_otsu_threshold(extract_intensity(constant_gray_rgb), "c" * 64)
    assert outcome.status == "unavailable"
    assert outcome.threshold is None
    assert "split" in outcome.reason


def test_otsu_is_deterministic_and_does_not_mutate(two_level_gray_rgb):
    intensity = extract_intensity(two_level_gray_rgb)
    before = intensity.copy()
    thresholds = [compute_otsu_threshold(intensity, "d" * 64).threshold for _ in range(5)]
    assert thresholds == [20] * 5
    assert np.array_equal(intensity, before)
