"""Pure, vectorized conversion from uint8 RGB to continuous HSV.

Hue is expressed in degrees in ``[0, 360)``. Saturation and value are
percentages in ``[0, 100]``. Achromatic pixels use hue zero.
"""

import numpy as np

from ..models import validate_rgb


def rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    """Return a new float64 HSV array for a validated RGB image.

    The implementation follows the max/min/delta equations in the processing
    contract. Divisions are evaluated only for pixels whose denominator is
    nonzero; no epsilon or rounding changes interval membership later.
    """
    validate_rgb(rgb)
    normalized = rgb.astype(np.float64) / 255.0
    red = normalized[..., 0]
    green = normalized[..., 1]
    blue = normalized[..., 2]

    maximum = np.max(normalized, axis=2)
    minimum = np.min(normalized, axis=2)
    delta = maximum - minimum

    saturation = np.zeros_like(maximum)
    nonblack = maximum != 0.0
    np.divide(delta, maximum, out=saturation, where=nonblack)

    hue = np.zeros_like(maximum)
    chromatic = delta != 0.0
    red_max = chromatic & (maximum == red)
    green_max = chromatic & ~red_max & (maximum == green)
    blue_max = chromatic & ~red_max & ~green_max

    ratio = np.zeros_like(maximum)
    np.divide(green - blue, delta, out=ratio, where=red_max)
    hue[red_max] = np.mod(ratio[red_max], 6.0)
    np.divide(blue - red, delta, out=ratio, where=green_max)
    hue[green_max] = ratio[green_max] + 2.0
    np.divide(red - green, delta, out=ratio, where=blue_max)
    hue[blue_max] = ratio[blue_max] + 4.0
    hue = np.mod(hue * 60.0, 360.0)

    return np.stack((hue, saturation * 100.0, maximum * 100.0), axis=2)
