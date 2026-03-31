from __future__ import annotations

import json
from pathlib import Path

from .models import GameState, SaveGamePayload
from .utils import default_paths


def save_game(state: GameState, filename: str, saves_dir: Path | None = None) -> Path:
    root = saves_dir or default_paths().saves_dir
    root.mkdir(parents=True, exist_ok=True)
    path = root / filename
    payload = SaveGamePayload(state=state)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload.model_dump(mode="json"), handle, indent=2)
    return path


def load_game(filename: str, saves_dir: Path | None = None) -> GameState:
    root = saves_dir or default_paths().saves_dir
    path = root / filename
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    payload = SaveGamePayload.model_validate(data)
    return payload.state
