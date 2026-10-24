"""Typed domain errors. Constructing an error never opens a file or a dialog."""

from pathlib import Path


class HSVSegmentationError(Exception):
    """Base class for recoverable application failures."""


class ValidationError(HSVSegmentationError, ValueError):
    """A named input field violates its data contract."""

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"{field}: {message}")


class FileOperationError(HSVSegmentationError):
    """File-operation context for an adapter or GUI to report to the user."""

    default_operation = "file operation"

    def __init__(self, message: str, *, path: str | Path | None = None,
                 operation: str | None = None):
        self.path = Path(path) if path is not None else None
        self.operation = operation or self.default_operation
        location = f" ({self.path})" if self.path is not None else ""
        super().__init__(f"{self.operation}: {message}{location}")


class InputError(FileOperationError):
    """A source cannot be opened or is unsupported."""

    default_operation = "open input"


class DecodeError(InputError):
    """An opened image or video cannot be decoded."""

    default_operation = "decode input"


class WriteError(FileOperationError):
    """An output or experiment record could not be written."""

    default_operation = "write output"
