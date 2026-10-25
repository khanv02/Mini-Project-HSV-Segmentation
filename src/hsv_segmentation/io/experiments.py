"""Atomic, versioned publication of reproducible segmentation experiments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from uuid import UUID, uuid4

import numpy as np

from ..errors import ValidationError, WriteError
from ..models import SegmentationResult
from .export import save_mask_png, save_result_png


@dataclass(frozen=True, slots=True)
class ExperimentReceipt:
    """Identity and location of one completely published experiment run."""

    run_id: UUID
    run_dir: Path
    record_path: Path


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as error:
        raise WriteError(
            f"could not hash required file ({error}); check that it is readable and retry",
            path=path,
            operation="record experiment",
        ) from error
    return digest.hexdigest()


def pixel_sha256(array: np.ndarray) -> str:
    """Hash decoded uint8 pixels with an explicit shape/channel prefix."""
    if not isinstance(array, np.ndarray) or array.dtype != np.uint8:
        raise ValidationError("artifact", "must be a uint8 NumPy array")
    if array.ndim == 2 and min(array.shape, default=0) > 0:
        height, width = array.shape
        prefix = f"uint8|{height}|{width}|1|L\n"
    elif array.ndim == 3 and array.shape[2] == 3 and min(array.shape[:2], default=0) > 0:
        height, width = array.shape[:2]
        prefix = f"uint8|{height}|{width}|3|RGB\n"
    else:
        raise ValidationError("artifact", "must be nonempty L or RGB pixels")
    digest = hashlib.sha256(prefix.encode("utf-8"))
    digest.update(np.ascontiguousarray(array).tobytes(order="C"))
    return digest.hexdigest()


def _nonempty(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(field, "must be nonempty text")
    return value.strip()


def _relative_path(target: Path, base: Path) -> str:
    try:
        return Path(os.path.relpath(target, base)).as_posix()
    except ValueError:
        return str(target)


def _write_record(record: dict, destination: Path) -> None:
    temporary = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        os.replace(temporary, destination)
    except (OSError, TypeError, ValueError) as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise WriteError(
            f"could not publish record.json ({error}); check the destination and retry",
            path=destination,
            operation="record experiment",
        ) from error


def publish_experiment(
    snapshot: SegmentationResult,
    lighting: str,
    observations: str,
    runs_dir: str | Path,
    environment_path: str | Path,
) -> ExperimentReceipt:
    """Publish PNG artifacts and record.json for one immutable result snapshot."""
    if not isinstance(snapshot, SegmentationResult):
        raise ValidationError("snapshot", "must be a complete segmentation result")
    lighting = _nonempty(lighting, "lighting")
    observations = _nonempty(observations, "observations")
    try:
        root = Path(runs_dir).resolve()
        environment = Path(environment_path).resolve()
    except (OSError, TypeError, ValueError) as error:
        raise WriteError(
            f"invalid experiment destination ({error}); choose a local directory and retry",
            path=runs_dir if isinstance(runs_dir, (str, Path)) else None,
            operation="record experiment",
        ) from error
    if not environment.is_file():
        raise WriteError(
            "environment record is missing; create experiments/environment.json first",
            path=environment,
            operation="record experiment",
        )

    run_id = uuid4()
    run_dir = root / str(run_id)
    try:
        root.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir(exist_ok=False)
    except OSError as error:
        raise WriteError(
            f"could not create a unique run directory ({error}); check permissions and retry",
            path=run_dir,
            operation="record experiment",
        ) from error

    mask_path = run_dir / "mask.png"
    result_path = run_dir / "result.png"
    record_path = run_dir / "record.json"
    try:
        save_mask_png(snapshot.mask, mask_path)
        save_result_png(snapshot.segmented_rgb, result_path)
        record = {
            "schema_version": 1,
            "run_id": str(run_id),
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": {
                "path": _relative_path(snapshot.source.source_path, run_dir),
                "sha256": snapshot.source.source_sha256,
                "media_kind": snapshot.source.media_kind,
                "width": snapshot.width,
                "height": snapshot.height,
                "frame_index": snapshot.frame_index,
                "backend": snapshot.source.backend,
            },
            "thresholds": snapshot.thresholds.as_dict(),
            "lighting": lighting,
            "observations": observations,
            "artifacts": {
                "mask": {
                    "path": "mask.png",
                    "sha256": _file_sha256(mask_path),
                    "pixel_sha256": pixel_sha256(snapshot.mask),
                },
                "result": {
                    "path": "result.png",
                    "sha256": _file_sha256(result_path),
                    "pixel_sha256": pixel_sha256(snapshot.segmented_rgb),
                },
            },
            "environment": {
                "path": _relative_path(environment, run_dir),
                "sha256": _file_sha256(environment),
            },
        }
        _write_record(record, record_path)
    except BaseException as error:
        if isinstance(error, (ValidationError, WriteError)):
            raise
        raise WriteError(
            f"experiment publication failed ({error}); inspect the partial run and retry",
            path=run_dir,
            operation="record experiment",
        ) from error
    return ExperimentReceipt(run_id, run_dir, record_path)
