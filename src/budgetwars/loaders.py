from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, TypeAdapter

from .models import (
    ContentBundle,
    EventDefinition,
    ExpenseDefinition,
    GameConfig,
    ItemDefinition,
    JobDefinition,
    LocationDefinition,
    PresetDefinition,
    ScoringDefinition,
)
from .utils import default_paths
from .validators import validate_content_bundle

ModelT = TypeVar("ModelT", bound=BaseModel)


def _read_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_model(path: Path, model_type: type[ModelT]) -> ModelT:
    data = _read_json(path)
    return model_type.model_validate(data)


def _load_model_list(path: Path, model_type: type[ModelT]) -> list[ModelT]:
    data = _read_json(path)
    adapter = TypeAdapter(list[model_type])
    return adapter.validate_python(data)


def load_config(data_dir: Path | None = None) -> GameConfig:
    root = data_dir or default_paths().data_dir
    return _load_model(root / "config.json", GameConfig)


def load_items(data_dir: Path | None = None) -> list[ItemDefinition]:
    root = data_dir or default_paths().data_dir
    return _load_model_list(root / "items.json", ItemDefinition)


def load_expenses(data_dir: Path | None = None) -> list[ExpenseDefinition]:
    root = data_dir or default_paths().data_dir
    return _load_model_list(root / "expenses.json", ExpenseDefinition)


def load_jobs(data_dir: Path | None = None) -> list[JobDefinition]:
    root = data_dir or default_paths().data_dir
    return _load_model_list(root / "jobs.json", JobDefinition)


def load_locations(data_dir: Path | None = None) -> list[LocationDefinition]:
    root = data_dir or default_paths().data_dir
    return _load_model_list(root / "locations.json", LocationDefinition)


def load_events(data_dir: Path | None = None) -> list[EventDefinition]:
    root = data_dir or default_paths().data_dir
    return _load_model_list(root / "events.json", EventDefinition)


def load_presets(data_dir: Path | None = None) -> list[PresetDefinition]:
    root = data_dir or default_paths().data_dir
    return _load_model_list(root / "presets.json", PresetDefinition)


def load_scoring(data_dir: Path | None = None) -> ScoringDefinition:
    root = data_dir or default_paths().data_dir
    return _load_model(root / "scoring.json", ScoringDefinition)


def load_all_content(data_dir: Path | None = None) -> ContentBundle:
    root = data_dir or default_paths().data_dir
    bundle = ContentBundle(
        config=load_config(root),
        items=load_items(root),
        expenses=load_expenses(root),
        jobs=load_jobs(root),
        locations=load_locations(root),
        events=load_events(root),
        presets=load_presets(root),
        scoring=load_scoring(root),
    )
    validate_content_bundle(bundle)
    return bundle
