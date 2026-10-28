"""Strict lossless ground-truth decoding and frame binding."""

from hashlib import sha256
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

from ..errors import DecodeError, InputError, ValidationError
from ..models import GroundTruth, InputMedia


def _hash_bytes(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _pixel_hash(mask: np.ndarray) -> str:
    prefix = f"uint8|{mask.shape[0]}|{mask.shape[1]}|1|L\n".encode()
    return sha256(prefix + np.ascontiguousarray(mask).tobytes()).hexdigest()


def load_ground_truth(
    path: str | Path, source: InputMedia, *, threshold: int = 0, truth_revision: int = 0
) -> GroundTruth:
    if not isinstance(source, InputMedia):
        raise ValidationError("source", "must be InputMedia")
    if isinstance(threshold, bool) or not isinstance(threshold, int) or not 0 <= threshold <= 254:
        raise ValidationError("truth_threshold", "must be an integer in 0..254")
    target = Path(path).resolve()
    if target.suffix.lower() not in {".png", ".bmp"}:
        raise InputError("ground truth must be lossless PNG or BMP", path=target, operation="load ground truth")
    try:
        with Image.open(target) as image:
            if (image.format or "").upper() not in {"PNG", "BMP"}:
                raise InputError("ground truth must be PNG or BMP", path=target, operation="load ground truth")
            if image.mode not in {"1", "L", "LA", "P", "RGB", "RGBA"}:
                raise InputError("unsupported ground-truth bit depth or mode", path=target, operation="load ground truth")
            image.load()
            alpha_ignored = image.mode in {"LA", "RGBA"}
            if image.mode == "1":
                gray = np.asarray(image.convert("L"), dtype=np.uint8)
            elif image.mode in {"L", "LA"}:
                gray = np.asarray(image.getchannel(0), dtype=np.uint8)
            else:
                rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
                if not (np.array_equal(rgb[..., 0], rgb[..., 1]) and np.array_equal(rgb[..., 1], rgb[..., 2])):
                    raise InputError("ground-truth RGB channels must be equal", path=target, operation="load ground truth")
                gray = rgb[..., 0]
    except (InputError, ValidationError):
        raise
    except FileNotFoundError as error:
        raise InputError("ground-truth file was not found", path=target, operation="load ground truth") from error
    except (OSError, UnidentifiedImageError, SyntaxError) as error:
        raise DecodeError("ground truth could not be decoded", path=target, operation="load ground truth") from error
    if gray.shape != (source.height, source.width):
        raise ValidationError(
            "ground_truth", f"dimensions {gray.shape[::-1]} must match source {(source.width, source.height)}"
        )
    mask = np.where(gray > threshold, 255, 0).astype(np.uint8)
    try:
        file_hash = _hash_bytes(target)
    except OSError as error:
        raise InputError("ground truth could not be read", path=target, operation="load ground truth") from error
    return GroundTruth(
        mask, target, file_hash, _pixel_hash(mask), threshold, alpha_ignored,
        source.session_id, source.source_sha256, source.frame_index, truth_revision,
    )
