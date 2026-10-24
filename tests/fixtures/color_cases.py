"""Independent analytical data for the later HSV processing tests.

No production module is imported. Expected masks are explicitly specified, not
computed by a duplicate segmentation function. Every factory returns new arrays.
HSV arrays use float64 degrees/percent, and conversion tolerances never expand
the exact interval membership represented by the expected masks.
"""

import colorsys
from dataclasses import dataclass
from typing import Final

import numpy as np


ABS_HUE_TOLERANCE_DEG: Final = 1e-10
ABS_SV_TOLERANCE_PCT: Final = 1e-10
RELATIVE_TOLERANCE: Final = 0.0
REFERENCE_SEED: Final = 20261024


@dataclass(frozen=True)
class ColorReference:
    name: str
    rgb: np.ndarray
    expected_hsv: np.ndarray
    labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class MaskReference:
    name: str
    hsv: np.ndarray
    bounds: dict[str, int]
    expected_mask: np.ndarray


def analytical_colors() -> ColorReference:
    """Primaries, secondaries, neutrals and colors immediately around red's origin."""
    labels = (
        "red", "green", "blue", "yellow", "cyan", "magenta", "black", "white",
        "gray_128", "red_below_origin", "red_above_origin", "dark_red",
    )
    rgb = np.array([[
        [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [0, 255, 255],
        [255, 0, 255], [0, 0, 0], [255, 255, 255], [128, 128, 128],
        [255, 0, 1], [255, 1, 0], [128, 0, 0],
    ]], dtype=np.uint8)
    hsv = np.array([[
        [0, 100, 100], [120, 100, 100], [240, 100, 100], [60, 100, 100],
        [180, 100, 100], [300, 100, 100], [0, 0, 0], [0, 0, 100],
        [0, 0, 12800 / 255], [360 - 60 / 255, 100, 100],
        [60 / 255, 100, 100], [0, 100, 12800 / 255],
    ]], dtype=np.float64)
    return ColorReference("analytical_colors", rgb, hsv, labels)


def colorsys_sample(seed: int = REFERENCE_SEED) -> ColorReference:
    """A deterministic 16x16 RGB sample with an independent stdlib scalar oracle."""
    generator = np.random.default_rng(seed)
    rgb = generator.integers(0, 256, size=(16, 16, 3), dtype=np.uint8)
    expected = np.array([
        colorsys.rgb_to_hsv(*(pixel / 255.0)) for pixel in rgb.reshape(-1, 3)
    ], dtype=np.float64).reshape(rgb.shape)
    expected *= [360.0, 100.0, 100.0]
    return ColorReference(f"colorsys_seed_{seed}", rgb, expected)


def _bounds(**changes) -> dict[str, int]:
    bounds = dict(lower_h_deg=0, upper_h_deg=360, lower_s_pct=0,
                  upper_s_pct=100, lower_v_pct=0, upper_v_pct=100)
    bounds.update(changes)
    return bounds


def _boundary_case(name: str, channel: int, lower: int, upper: int) -> MaskReference:
    values = np.array([
        np.nextafter(float(lower), -np.inf), float(lower),
        np.nextafter(float(lower), np.inf), np.nextafter(float(upper), -np.inf),
        float(upper), np.nextafter(float(upper), np.inf),
    ])
    hsv = np.tile(np.array([90.0, 50.0, 50.0]), (1, 6, 1))
    hsv[0, :, channel] = values
    names = (("lower_h_deg", "upper_h_deg"), ("lower_s_pct", "upper_s_pct"),
             ("lower_v_pct", "upper_v_pct"))
    low_name, high_name = names[channel]
    return MaskReference(name, hsv, _bounds(**{low_name: lower, high_name: upper}),
                         np.array([[0, 255, 255, 255, 255, 0]], dtype=np.uint8))


def threshold_cases() -> tuple[MaskReference, ...]:
    """Eleven exact membership cases, including adjacent representable floats."""
    wrap = np.array([[
        [np.nextafter(350.0, -np.inf), 50, 50], [350, 50, 50],
        [np.nextafter(350.0, np.inf), 50, 50], [359.9, 50, 50],
        [0, 50, 50], [10, 50, 50], [np.nextafter(10.0, np.inf), 50, 50],
        [180, 50, 50],
    ]], dtype=np.float64)
    zero_only = np.array([[[0, 50, 50], [np.nextafter(0.0, np.inf), 50, 50],
                           [359.9, 50, 50]]], dtype=np.float64)
    near_red = np.array([[[0, 100, 100], [360 - 60 / 255, 100, 100]]], dtype=np.float64)
    full = np.array([[[0, 0, 0], [359.999, 100, 100], [180, 50, 50]]], dtype=np.float64)
    none = np.array([[[0, 50, 50], [60, 50, 50], [120, 50, 50]]], dtype=np.float64)
    equal_hue = np.array([[[np.nextafter(90.0, -np.inf), 50, 50], [90, 50, 50],
                           [np.nextafter(90.0, np.inf), 50, 50]]], dtype=np.float64)
    equal_s = np.array([[[0, np.nextafter(100.0, -np.inf), 100], [0, 100, 100]]],
                       dtype=np.float64)
    equal_v = np.array([[[0, 100, np.nextafter(100.0, -np.inf)], [0, 100, 100]]],
                       dtype=np.float64)
    return (
        _boundary_case("hue_endpoints", 0, 60, 120),
        _boundary_case("saturation_endpoints", 1, 20, 80),
        _boundary_case("value_endpoints", 2, 10, 90),
        MaskReference("hue_wraparound", wrap, _bounds(lower_h_deg=350, upper_h_deg=10),
                      np.array([[0, 255, 255, 255, 255, 255, 0, 0]], dtype=np.uint8)),
        MaskReference("hue_zero_only", zero_only, _bounds(upper_h_deg=0),
                      np.array([[255, 0, 0]], dtype=np.uint8)),
        MaskReference("upper_359_excludes_near_red", near_red, _bounds(upper_h_deg=359),
                      np.array([[255, 0]], dtype=np.uint8)),
        MaskReference("full_domain", full, _bounds(), np.full((1, 3), 255, dtype=np.uint8)),
        MaskReference("no_selection", none, _bounds(lower_h_deg=90, upper_h_deg=90),
                      np.zeros((1, 3), dtype=np.uint8)),
        MaskReference("equal_hue", equal_hue, _bounds(lower_h_deg=90, upper_h_deg=90),
                      np.array([[0, 255, 0]], dtype=np.uint8)),
        MaskReference("equal_saturation", equal_s, _bounds(lower_s_pct=100),
                      np.array([[0, 255]], dtype=np.uint8)),
        MaskReference("equal_value", equal_v, _bounds(lower_v_pct=100),
                      np.array([[0, 255]], dtype=np.uint8)),
    )


def red_extraction_reference() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Expected mask/RGB for H=(350,10), S=(50,100), V=(0,100), specified literally."""
    rgb = analytical_colors().rgb
    mask = np.array([[255, 0, 0, 0, 0, 0, 0, 0, 0, 255, 255, 255]], dtype=np.uint8)
    extracted = np.array([[
        [255, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0],
        [0, 0, 0], [0, 0, 0], [0, 0, 0], [255, 0, 1], [255, 1, 0], [128, 0, 0],
    ]], dtype=np.uint8)
    return rgb, mask, extracted
