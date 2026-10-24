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


def _cause_and_action(error: BaseException) -> tuple[str, str]:
    """Map a typed failure to a truthful user-facing category and next action."""
    message = str(error).lower()
    if isinstance(error, WriteError):
        return (
            "write failure",
            "Check the destination path and permissions, choose another PNG destination if needed, and retry.",
        )
    if isinstance(error, DecodeError):
        return (
            "decode failure",
            "Reopen the file or choose a supported, non-corrupt PNG/JPEG/BMP image or MP4/AVI video.",
        )
    if isinstance(error, InputError):
        if "not found" in message or "missing" in message:
            return "missing input", "Check the path and choose an existing local file."
        if "permission" in message or "unreadable" in message or "could not read" in message:
            return "unreadable input", "Check file permissions and choose a readable local file."
        if "unsupported" in message or "file type" in message or "mode" in message:
            return (
                "unsupported input",
                "Choose a readable PNG, JPEG, or BMP image, or a locally decodable MP4 or AVI video.",
            )
        if any(word in message for word in ("pixel limit", "memory", "safety limit", "allocation")):
            return "resource limit", "Choose a smaller input and retry."
        return "input failure", "Check the local file, its format, and permissions, then retry."
    if isinstance(error, ValidationError):
        return "invalid parameter", "Enter a value within the displayed range and ordering rule."
    return "unexpected failure", "Retry the operation; if it repeats, choose another local input or destination."


def format_recovery_message(
    error: BaseException,
    *,
    preserved_state: str,
    operation: str | None = None,
    affected: str | Path | None = None,
) -> str:
    """Produce the five FR-013 fields without inventing an uncertain diagnosis."""
    cause, action = _cause_and_action(error)
    resolved_operation = operation or getattr(error, "operation", "application operation")
    resolved_affected = affected or getattr(error, "path", None) or getattr(
        error, "field", "current session"
    )
    return (
        f"Operation: {resolved_operation}. "
        f"Affected: {resolved_affected}. "
        f"Cause: {cause}. "
        f"Details: {error}. "
        f"Preserved: {preserved_state.strip()} "
        f"Action: {action}"
    )
