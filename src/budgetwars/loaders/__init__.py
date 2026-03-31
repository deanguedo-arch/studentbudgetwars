from pathlib import Path

from .content_loader import load_content_bundle
from .validators import validate_content_bundle


def load_all_content(root: Path | None = None):
    project_root = root or Path(__file__).resolve().parents[3]
    return load_content_bundle(project_root / "data")


__all__ = ["load_all_content", "load_content_bundle", "validate_content_bundle"]
