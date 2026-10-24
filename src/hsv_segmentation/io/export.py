"""Lossless PNG output adapters for immutable segmentation snapshots."""

from dataclasses import dataclass
import os
from pathlib import Path
from uuid import uuid4

import numpy as np
from PIL import Image

from ..errors import WriteError
from ..models import SegmentationResult, validate_rgb


@dataclass(frozen=True, slots=True)
class ExportReceipt:
    """Identity of one completed write, independent of the current GUI session."""

    kind: str
    path: Path
    source_path: Path
    session_id: str
    frame_index: int | None


def _validate_destination(path: str | Path, operation: str) -> Path:
    try:
        target = Path(path).resolve()
    except (OSError, TypeError, ValueError) as error:
        raise WriteError(
            f"invalid destination; choose a local PNG path ({error})",
            path=path if isinstance(path, (str, Path)) else None,
            operation=operation,
        ) from error
    if target.suffix.lower() != ".png":
        raise WriteError(
            "destination must use the .png extension; choose a PNG path",
            path=target,
            operation=operation,
        )
    return target


def _write_png(
    array: np.ndarray,
    path: str | Path,
    *,
    mode: str,
    operation: str,
    overwrite: bool,
) -> Path:
    target = _validate_destination(path, operation)
    if target.exists() and not overwrite:
        raise WriteError(
            "destination already exists; confirm overwrite or choose another path",
            path=target,
            operation=operation,
        )
    temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    try:
        target.parent.mkdir(parents=False, exist_ok=True)
        Image.fromarray(array, mode=mode).save(temporary, format="PNG")
        os.replace(temporary, target)
    except (OSError, ValueError) as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise WriteError(
            f"could not write PNG ({error}); check the destination and permissions, then retry",
            path=target,
            operation=operation,
        ) from error
    return target


def save_mask_png(
    mask: np.ndarray, path: str | Path, *, overwrite: bool = False
) -> Path:
    """Atomically save a source-resolution uint8 0/255 mask as PNG L."""
    operation = "save mask PNG"
    if (
        not isinstance(mask, np.ndarray)
        or mask.dtype != np.uint8
        or mask.ndim != 2
        or min(mask.shape, default=0) == 0
        or not np.all((mask == 0) | (mask == 255))
    ):
        raise WriteError(
            "invalid output data; mask must be a nonempty uint8 array containing only 0 and 255",
            path=path,
            operation=operation,
        )
    return _write_png(mask, path, mode="L", operation=operation, overwrite=overwrite)


def save_result_png(
    rgb: np.ndarray, path: str | Path, *, overwrite: bool = False
) -> Path:
    """Atomically save a source-resolution uint8 RGB result as PNG RGB."""
    operation = "save result PNG"
    try:
        validate_rgb(rgb)
    except (TypeError, ValueError) as error:
        raise WriteError(
            f"invalid output data; result must be a nonempty uint8 RGB array ({error})",
            path=path,
            operation=operation,
        ) from error
    return _write_png(rgb, path, mode="RGB", operation=operation, overwrite=overwrite)


def export_snapshot(
    snapshot: SegmentationResult,
    kind: str,
    path: str | Path,
    *,
    overwrite: bool = False,
) -> ExportReceipt:
    """Write one immutable mask/result snapshot and return its captured identity."""
    if not isinstance(snapshot, SegmentationResult):
        raise WriteError("invalid output data; no complete result snapshot", operation="export")
    if kind == "mask":
        saved = save_mask_png(snapshot.mask, path, overwrite=overwrite)
    elif kind == "result":
        saved = save_result_png(snapshot.segmented_rgb, path, overwrite=overwrite)
    else:
        raise WriteError(f"unsupported output kind {kind!r}", path=path, operation="export")
    return ExportReceipt(
        kind=kind,
        path=saved,
        source_path=snapshot.source.source_path,
        session_id=snapshot.session_id,
        frame_index=snapshot.frame_index,
    )
