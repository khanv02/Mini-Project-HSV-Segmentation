"""Check the independent reference data, not the unimplemented HSV algorithm."""

import colorsys
import subprocess
import sys

import numpy as np

from tests.fixtures.color_cases import (
    ABS_HUE_TOLERANCE_DEG,
    ABS_SV_TOLERANCE_PCT,
    RELATIVE_TOLERANCE,
    analytical_colors,
    colorsys_sample,
    red_extraction_reference,
    threshold_cases,
)


def test_hand_derived_colors_agree_with_independent_scalar_reference():
    case = analytical_colors()
    assert case.rgb.shape == case.expected_hsv.shape == (1, 12, 3)
    assert case.rgb.dtype == np.uint8 and case.expected_hsv.dtype == np.float64
    assert len(case.labels) == 12
    reference = np.array([
        colorsys.rgb_to_hsv(*(pixel / 255.0)) for pixel in case.rgb.reshape(-1, 3)
    ]).reshape(case.expected_hsv.shape) * [360.0, 100.0, 100.0]
    hue_error = np.abs((case.expected_hsv[..., 0] - reference[..., 0] + 180) % 360 - 180)
    assert np.all(hue_error <= ABS_HUE_TOLERANCE_DEG)
    np.testing.assert_allclose(case.expected_hsv[..., 1:], reference[..., 1:],
                               atol=ABS_SV_TOLERANCE_PCT, rtol=RELATIVE_TOLERANCE)
    near_red_index = case.labels.index("red_below_origin")
    assert 359 < case.expected_hsv[0, near_red_index, 0] < 360


def test_sampling_is_repeatable_and_does_not_share_array_storage():
    first, second = colorsys_sample(), colorsys_sample()
    np.testing.assert_array_equal(first.rgb, second.rgb)
    np.testing.assert_array_equal(first.expected_hsv, second.expected_hsv)
    assert first.rgb.shape == first.expected_hsv.shape == (16, 16, 3)
    assert np.isfinite(first.expected_hsv).all()
    assert ((first.expected_hsv[..., 0] >= 0) & (first.expected_hsv[..., 0] < 360)).all()
    assert ((first.expected_hsv[..., 1:] >= 0) & (first.expected_hsv[..., 1:] <= 100)).all()
    first.rgb.fill(0)
    assert np.any(second.rgb)


def test_boundary_references_specify_the_exact_adjacent_float_membership():
    cases = {case.name: case for case in threshold_cases()}
    assert len(cases) == 11
    for name, channel, lower, upper in [
        ("hue_endpoints", 0, 60, 120),
        ("saturation_endpoints", 1, 20, 80),
        ("value_endpoints", 2, 10, 90),
    ]:
        case = cases[name]
        values = case.hsv[0, :, channel]
        assert values[0] < lower == values[1] < values[2]
        assert values[3] < upper == values[4] < values[5]
        np.testing.assert_array_equal(case.expected_mask, [[0, 255, 255, 255, 255, 0]])
    np.testing.assert_array_equal(cases["hue_wraparound"].expected_mask,
                                  [[0, 255, 255, 255, 255, 255, 0, 0]])
    np.testing.assert_array_equal(cases["hue_zero_only"].expected_mask, [[255, 0, 0]])
    np.testing.assert_array_equal(cases["upper_359_excludes_near_red"].expected_mask, [[255, 0]])
    assert np.all(cases["full_domain"].expected_mask == 255)
    assert np.all(cases["no_selection"].expected_mask == 0)
    for case in cases.values():
        assert case.hsv.dtype == np.float64 and np.isfinite(case.hsv).all()
        assert case.expected_mask.dtype == np.uint8
        assert case.expected_mask.shape == case.hsv.shape[:2]
        assert set(np.unique(case.expected_mask)) <= {0, 255}


def test_expected_extracted_red_colors_are_literal_source_values():
    rgb, mask, extracted = red_extraction_reference()
    assert rgb.shape == extracted.shape == (1, 12, 3)
    assert mask.shape == (1, 12)
    np.testing.assert_array_equal(mask, [[255, 0, 0, 0, 0, 0, 0, 0, 0, 255, 255, 255]])
    np.testing.assert_array_equal(extracted[mask == 255], rgb[mask == 255])
    assert not np.any(extracted[mask == 0])
    assert all(array.dtype == np.uint8 for array in (rgb, mask, extracted))


def test_fixtures_do_not_import_any_production_implementation():
    subprocess.run([sys.executable, "-c", (
        "import sys; import tests.fixtures.color_cases; "
        "assert not any(n == 'hsv_segmentation' or n.startswith('hsv_segmentation.') "
        "for n in sys.modules)"
    )], check=True)
