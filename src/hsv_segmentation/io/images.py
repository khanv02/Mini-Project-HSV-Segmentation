"""Pillow adapter for supported still-image inputs."""

from hashlib import sha256
from pathlib import Path
import warnings

import numpy as np
from PIL import Image, UnidentifiedImageError

from ..errors import DecodeError, InputError
from ..models import InputMedia, MAX_IMAGE_PIXELS


SUPPORTED_IMAGE_FORMATS = frozenset({"PNG", "JPEG", "BMP"})
SUPPORTED_IMAGE_MODES = frozenset({"L", "LA", "RGB", "RGBA", "P"})
SUPPORTED_INPUT_MESSAGE = "choose a readable PNG, JPEG, or BMP image"


def _read_source_hash(path: Path) -> str:
    digest = sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise InputError(
            f"could not read the file; {SUPPORTED_INPUT_MESSAGE}", path=path
        ) from error
    return digest.hexdigest()


def load_image(path: str | Path) -> InputMedia:
    """Fully decode and normalize one image before returning a media snapshot.

    Supported 8-bit modes are L, LA, RGB, RGBA and P. Alpha is ignored rather
    than composited, and stored orientation is retained without EXIF rotation.
    """
    source_path = Path(path).resolve()
    if source_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
        raise InputError(f"unsupported file type; {SUPPORTED_INPUT_MESSAGE}", path=source_path)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(source_path) as image:
                source_format = (image.format or "").upper()
                if source_format not in SUPPORTED_IMAGE_FORMATS:
                    raise InputError(
                        f"unsupported image format; {SUPPORTED_INPUT_MESSAGE}", path=source_path
                    )
                width, height = image.size
                if width <= 0 or height <= 0:
                    raise DecodeError("image has empty dimensions", path=source_path)
                if width * height > MAX_IMAGE_PIXELS:
                    raise InputError(
                        f"image exceeds the {MAX_IMAGE_PIXELS:,}-pixel limit; use a smaller image",
                        path=source_path,
                    )
                if image.mode not in SUPPORTED_IMAGE_MODES:
                    raise InputError(
                        f"unsupported mode {image.mode!r}; use a standard 8-bit grayscale, palette, or RGB image",
                        path=source_path,
                    )
                image.load()
                try:
                    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8).copy()
                except (MemoryError, ValueError) as error:
                    raise InputError(
                        "not enough memory to normalize the image; use a smaller image",
                        path=source_path,
                    ) from error
    except InputError:
        raise
    except FileNotFoundError as error:
        raise InputError(
            f"file was not found; {SUPPORTED_INPUT_MESSAGE}", path=source_path
        ) from error
    except PermissionError as error:
        raise InputError(
            f"permission denied; check access and {SUPPORTED_INPUT_MESSAGE}", path=source_path
        ) from error
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as error:
        raise DecodeError(
            f"image could not be decoded; {SUPPORTED_INPUT_MESSAGE}", path=source_path
        ) from error
    except Image.DecompressionBombWarning as error:
        raise InputError(
            "image triggered Pillow's safety limit; use a smaller image", path=source_path
        ) from error

    return InputMedia(
        source_path=source_path,
        source_sha256=_read_source_hash(source_path),
        source_format=source_format,
        rgb=rgb,
    )
