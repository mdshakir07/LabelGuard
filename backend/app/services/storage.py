import hashlib
import io
import re
import shutil
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException, status
from PIL import Image

from ..config import get_settings

DEFAULT_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
MAX_DIM = 8000


def _sanitize_name(name: str) -> str:
    clean = DEFAULT_NAME_RE.sub("_", name).strip("._")
    return clean or "image"


def _fs(rel: str) -> Path:
    return Path(get_settings().resolved_storage_root) / rel


def relative_url(inspection_id: int, src: str, name: str) -> str:
    return f"{inspection_id}/{src}/{name}"


def build_paths(inspection_id: int, typ: str, filename: str) -> Tuple[str, str]:
    stem = re.sub(r"\.[A-Za-z0-9]+$", "", _sanitize_name(filename))[:60]
    name = f"{typ}_{stem}.img"
    rel = relative_url(inspection_id, "original", name)
    return rel, relative_url(inspection_id, "processed", name)


def validate_and_store(contents: bytes, filename: str, typ: str, inspection_id: int) -> dict:
    settings = get_settings()
    if len(contents) > settings.max_image_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"Image exceeds {settings.max_image_mb} MB limit")

    buf = io.BytesIO(contents)
    try:
        img = Image.open(buf)
        img.load()
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid or corrupt image")
    fmt = img.format
    img = img.convert("RGB")

    if img.width > MAX_DIM or img.height > MAX_DIM:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Image dimension exceeds {MAX_DIM}px")

    mimetype = Image.MIME.get(fmt or "", "") if fmt else ""
    if settings.allowed_image_types and mimetype not in settings.allowed_image_types:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Unsupported image type {mimetype or 'unknown'}")

    sha = hashlib.sha256(contents).hexdigest()
    rel, _ = build_paths(inspection_id, typ, filename)
    dst = _fs(rel)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(contents)

    return {"original_url": rel, "sha256": sha, "width": img.width, "height": img.height, "format": img.format}


def image_bytes(rel: str) -> bytes:
    if not rel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    path = _fs(rel).resolve()
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return path.read_bytes()


def update_processed_url(inspection_id: int, rel_original: str, new_rel: str) -> None:
    src = _fs(rel_original)
    dst = _fs(new_rel)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def delete_inspection_storage(inspection_id: int) -> None:
    shutil.rmtree(_fs(str(inspection_id)), ignore_errors=True)