from __future__ import annotations

import random
from pathlib import Path

from .models import FileSystemPaths


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_paths() -> FileSystemPaths:
    root = project_root()
    return FileSystemPaths(
        root=root,
        data_dir=root / "data",
        saves_dir=root / "saves",
    )


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def make_rng(seed: int | None = None) -> random.Random:
    return random.Random(seed)


def trim_messages(messages: list[str], limit: int) -> list[str]:
    if limit <= 0:
        return []
    return messages[-limit:]
