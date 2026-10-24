"""Validation boundary for the six user-facing HSV threshold values."""

from collections.abc import Mapping

from ..errors import ValidationError
from ..models import HSVThresholdSet, THRESHOLD_FIELDS


def validate_thresholds(
    thresholds: HSVThresholdSet | Mapping[str, object],
) -> HSVThresholdSet:
    """Return a validated immutable threshold set without clamping values.

    Existing :class:`HSVThresholdSet` snapshots retain their parameter
    revision. Mappings must contain exactly the six documented field names.
    """
    if isinstance(thresholds, HSVThresholdSet):
        return thresholds
    if not isinstance(thresholds, Mapping):
        raise ValidationError("thresholds", "must be a threshold set or six-field mapping")

    keys = set(thresholds)
    expected = set(THRESHOLD_FIELDS)
    if keys != expected:
        missing = sorted(expected - keys)
        extra = sorted(keys - expected)
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if extra:
            details.append(f"unexpected {', '.join(extra)}")
        raise ValidationError("thresholds", "; ".join(details))
    return HSVThresholdSet(**{name: thresholds[name] for name in THRESHOLD_FIELDS})
