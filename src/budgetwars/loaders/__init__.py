from __future__ import annotations

from pathlib import Path

from .content_loader import load_content_bundle
from .validators import validate_content_bundle


def load_all_content(root: Path | None = None, *, mode: str = "classic"):
    from budgetwars.core.content import load_mode_content

    project_root = root or Path(__file__).resolve().parents[3]
    return load_mode_content(project_root, mode)


__all__ = ["load_all_content", "load_content_bundle", "validate_content_bundle"]
