from __future__ import annotations

from pathlib import Path

from budgetwars.loaders.content_loader import load_content_bundle
from budgetwars.models import ContentBundle

from .startup import GameMode, normalize_mode


CONTENT_FILE_LAYOUT: tuple[str, ...] = (
    "config.json",
    "balance/difficulty_modifiers.json",
    "balance/scoring_weights.json",
    "cities.json",
    "careers.json",
    "education.json",
    "housing.json",
    "transport.json",
    "focus_actions.json",
    "wealth_strategies.json",
    "events.json",
    "presets.json",
)


def resolve_content_files(root: Path, mode: GameMode | str = "classic") -> dict[str, Path]:
    normalized_mode = normalize_mode(mode)
    shared_dir = root / "content" / "shared"
    legacy_dir = root / "data"
    mode_dir = root / "content" / normalized_mode
    resolved: dict[str, Path] = {}
    for relative in CONTENT_FILE_LAYOUT:
        mode_path = mode_dir / relative
        shared_path = shared_dir / relative
        legacy_path = legacy_dir / relative
        if mode_path.exists():
            resolved[relative] = mode_path
        elif shared_path.exists():
            resolved[relative] = shared_path
        elif legacy_path.exists():
            resolved[relative] = legacy_path
        else:
            raise FileNotFoundError(f"Unable to resolve required content file '{relative}' for mode '{normalized_mode}'.")
    return resolved


def load_mode_content(root: Path, mode: GameMode | str = "classic") -> ContentBundle:
    return load_content_bundle(content_files=resolve_content_files(root, mode))
