"""Domain failures must be distinguishable without a GUI."""

import pytest

from hsv_segmentation.errors import (
    DecodeError, HSVSegmentationError, InputError, ValidationError, WriteError,
)


def test_validation_error_retains_the_invalid_field():
    error = ValidationError("upper_h_deg", "must be an integer in 0..360")
    assert isinstance(error, HSVSegmentationError)
    assert isinstance(error, ValueError)
    assert error.field == "upper_h_deg"
    assert "upper_h_deg" in str(error) and "0..360" in str(error)


@pytest.mark.parametrize("kind,operation", [
    (InputError, "open input"), (DecodeError, "decode input"), (WriteError, "write output"),
])
def test_file_errors_preserve_context_without_accessing_the_file(kind, operation, tmp_path):
    path = tmp_path / "does-not-exist.png"
    error = kind("Check permissions or choose another file.", path=path)
    assert isinstance(error, HSVSegmentationError)
    assert error.path == path and error.operation == operation
    assert str(path) in str(error) and operation in str(error)
    assert "Check permissions" in str(error)
    assert not path.exists()


def test_decode_failure_is_a_specific_input_failure():
    assert isinstance(DecodeError("Unsupported encoding."), InputError)
    assert not isinstance(WriteError("Destination is unwritable."), InputError)
