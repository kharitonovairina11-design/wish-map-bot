import os
import uuid
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / "tmp"
TMP_DIR.mkdir(exist_ok=True)


def make_temp_path(suffix: str = ".png", prefix: Optional[str] = None) -> Path:
    name = f"{prefix or 'file'}-{uuid.uuid4().hex}{suffix}"
    return TMP_DIR / name


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def cleanup(path: Path) -> None:
    try:
        os.remove(path)
    except OSError:
        return



