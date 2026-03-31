from __future__ import annotations

import json
from pathlib import Path

from budgetwars.models import FileSystemPaths, GameState, SaveGamePayload


def default_paths(root: Path | None = None) -> FileSystemPaths:
    project_root = root or Path(__file__).resolve().parents[3]
    saves_dir = project_root / "saves"
    saves_dir.mkdir(parents=True, exist_ok=True)
    return FileSystemPaths(root=project_root, data_dir=project_root / "data", saves_dir=saves_dir)


def save_game(state: GameState, save_path: Path) -> Path:
    payload = SaveGamePayload(state=state)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    return save_path


def save_named_game(state: GameState, save_name: str, root: Path | None = None) -> Path:
    paths = default_paths(root)
    return save_game(state, paths.saves_dir / save_name)


def load_game(save_path: Path) -> GameState:
    payload = SaveGamePayload.model_validate(json.loads(save_path.read_text(encoding="utf-8")))
    return payload.state


def load_named_game(save_name: str, root: Path | None = None) -> GameState:
    paths = default_paths(root)
    return load_game(paths.saves_dir / save_name)
