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
from ..models import OverlaySnapshot, SegmentationResult
from .export import save_mask_png, save_overlay_png, save_result_png


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


def label_sha256(labels: np.ndarray) -> str:
    """Hash normalized int32 labels with explicit little-endian shape metadata."""
    if not isinstance(labels, np.ndarray) or labels.dtype != np.int32 or labels.ndim != 2:
        raise ValidationError("labels", "must be a two-dimensional int32 array")
    stable = np.ascontiguousarray(labels.astype("<i4", copy=False))
    prefix = f"int32-le|{stable.shape[0]}|{stable.shape[1]}\n".encode()
    return hashlib.sha256(prefix + stable.tobytes()).hexdigest()


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
    overlay: OverlaySnapshot | None = None,
) -> ExperimentReceipt:
    """Publish PNG artifacts and record.json for one immutable result snapshot."""
    if not isinstance(snapshot, SegmentationResult):
        raise ValidationError("snapshot", "must be a complete segmentation result")
    if overlay is not None:
        if not isinstance(overlay, OverlaySnapshot):
            raise ValidationError("overlay", "must be an OverlaySnapshot or None")
        if (overlay.session_id, overlay.frame_index, overlay.request_revision) != (
            snapshot.session_id, snapshot.frame_index, snapshot.request_revision
        ):
            raise ValidationError("overlay", "must match the segmentation snapshot identity")
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
        extended = (
            snapshot.analysis_settings.enabled
            or snapshot.watershed_settings.enabled
            or snapshot.evaluation is not None
        )
        schema_three = (
            snapshot.segmentation_mode == "grayscale"
            or overlay is not None
            or bool(snapshot.threshold_ranges)
        )
        record = {
            "schema_version": 3 if schema_three else (2 if extended else 1),
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
            "morphology": snapshot.morphology.as_dict(),
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
        if snapshot.threshold_ranges:
            record["threshold_ranges"] = [
                bounds.as_dict() for bounds in snapshot.threshold_ranges
            ]
        if schema_three:
            segmentation = {"mode": str(snapshot.segmentation_mode)}
            if snapshot.segmentation_mode == "grayscale":
                resolved = (
                    snapshot.otsu_outcome.threshold
                    if snapshot.otsu_outcome.status == "applied"
                    else snapshot.grayscale_settings.manual_threshold
                )
                segmentation.update(snapshot.grayscale_settings.as_dict(
                    resolved_threshold=resolved
                ))
                segmentation["eligibility"] = {
                    "rule": "exact_rgb_channel_equality", "eligible": True,
                }
                if snapshot.grayscale_settings.threshold_source == "otsu":
                    segmentation["tie_rule"] = snapshot.otsu_outcome.tie_rule
            record["segmentation"] = segmentation
        if overlay is not None:
            overlay_path = run_dir / "overlay.png"
            save_overlay_png(overlay.rgb, overlay_path)
            record["overlay"] = {
                "variant": overlay.variant,
                "display_settings": overlay.display_settings.as_dict(),
                "artifact": {
                    "path": overlay_path.name,
                    "sha256": _file_sha256(overlay_path),
                    "pixel_sha256": pixel_sha256(overlay.rgb),
                },
            }
            if overlay.truth_pixel_sha256 is not None:
                record["overlay"]["truth_pixel_sha256"] = overlay.truth_pixel_sha256
        if extended:
            if snapshot.analysis is not None:
                components_path = run_dir / "components_mask.png"
                save_mask_png(snapshot.analysis.filtered_mask, components_path)
                record["analysis"] = {
                    "settings": snapshot.analysis_settings.as_dict(),
                    "raw_count": snapshot.analysis.raw_count,
                    "retained_count": snapshot.analysis.retained_count,
                    "regions": [region.as_dict() for region in snapshot.analysis.regions],
                    "artifact": {
                        "path": components_path.name,
                        "sha256": _file_sha256(components_path),
                        "pixel_sha256": pixel_sha256(snapshot.analysis.filtered_mask),
                    },
                }
            if snapshot.watershed is not None:
                separation = snapshot.watershed
                water_record = {
                    "settings": snapshot.watershed_settings.as_dict(),
                    "status": separation.status,
                    "reason": separation.reason,
                    "ridge_pixels_excluded": True,
                }
                if separation.status in {"applied", "empty"}:
                    labels_path = run_dir / "watershed_labels.npy"
                    boundaries_path = run_dir / "watershed_boundaries.png"
                    water_mask_path = run_dir / "watershed_mask.png"
                    np.save(labels_path, separation.labels, allow_pickle=False)
                    save_mask_png(separation.boundaries, boundaries_path)
                    save_mask_png(separation.foreground_mask, water_mask_path)
                    water_record["artifacts"] = {
                        "labels": {
                            "path": labels_path.name, "sha256": _file_sha256(labels_path),
                            "label_sha256": label_sha256(separation.labels),
                            "dtype": "int32", "shape": list(separation.labels.shape),
                        },
                        "boundaries": {
                            "path": boundaries_path.name, "sha256": _file_sha256(boundaries_path),
                            "pixel_sha256": pixel_sha256(separation.boundaries),
                        },
                        "mask": {
                            "path": water_mask_path.name, "sha256": _file_sha256(water_mask_path),
                            "pixel_sha256": pixel_sha256(separation.foreground_mask),
                        },
                    }
                record["watershed"] = water_record
            if snapshot.evaluation is not None and snapshot.ground_truth is not None:
                if snapshot.evaluation_target == "components":
                    prediction = snapshot.analysis.filtered_mask
                elif snapshot.evaluation_target == "watershed":
                    prediction = snapshot.watershed.foreground_mask
                else:
                    prediction = snapshot.mask
                prediction_path = run_dir / "prediction.png"
                truth_path = run_dir / "ground_truth.png"
                save_mask_png(prediction, prediction_path)
                save_mask_png(snapshot.ground_truth.mask, truth_path)
                record["evaluation"] = {
                    **snapshot.evaluation.as_dict(),
                    "truth": {
                        "source_path": _relative_path(snapshot.ground_truth.source_path, run_dir),
                        "source_sha256": snapshot.ground_truth.source_sha256,
                        "normalized_pixel_sha256": snapshot.ground_truth.pixel_sha256,
                        "threshold": snapshot.ground_truth.threshold,
                        "alpha_ignored": snapshot.ground_truth.alpha_ignored,
                        "session_id": snapshot.ground_truth.session_id,
                        "frame_index": snapshot.ground_truth.frame_index,
                    },
                    "artifacts": {
                        "prediction": {
                            "path": prediction_path.name, "sha256": _file_sha256(prediction_path),
                            "pixel_sha256": pixel_sha256(prediction),
                        },
                        "ground_truth": {
                            "path": truth_path.name, "sha256": _file_sha256(truth_path),
                            "pixel_sha256": pixel_sha256(snapshot.ground_truth.mask),
                        },
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
