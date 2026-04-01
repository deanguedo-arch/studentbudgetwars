from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, TypeAdapter

from budgetwars.models import (
    AppConfig,
    CareerTrackDefinition,
    CityDefinition,
    ContentBundle,
    DifficultyModifier,
    EducationProgramDefinition,
    EventDefinition,
    FocusActionDefinition,
    HousingOptionDefinition,
    PresetDefinition,
    ScoringWeights,
    TransportOptionDefinition,
)

from .validators import validate_content_bundle

ModelT = TypeVar("ModelT", bound=BaseModel)


def _read_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_model(path: Path, model_type: type[ModelT]) -> ModelT:
    return model_type.model_validate(_read_json(path))


def _load_model_list(path: Path, model_type: type[ModelT]) -> list[ModelT]:
    adapter = TypeAdapter(list[model_type])
    return adapter.validate_python(_read_json(path))


def load_content_bundle(data_dir: Path) -> ContentBundle:
    bundle = ContentBundle(
        config=_load_model(data_dir / "config.json", AppConfig),
        difficulties=_load_model_list(data_dir / "balance" / "difficulty_modifiers.json", DifficultyModifier),
        scoring_weights=_load_model(data_dir / "balance" / "scoring_weights.json", ScoringWeights),
        cities=_load_model_list(data_dir / "cities.json", CityDefinition),
        careers=_load_model_list(data_dir / "careers.json", CareerTrackDefinition),
        education_programs=_load_model_list(data_dir / "education.json", EducationProgramDefinition),
        housing_options=_load_model_list(data_dir / "housing.json", HousingOptionDefinition),
        transport_options=_load_model_list(data_dir / "transport.json", TransportOptionDefinition),
        focus_actions=_load_model_list(data_dir / "focus_actions.json", FocusActionDefinition),
        events=_load_model_list(data_dir / "events.json", EventDefinition),
        presets=_load_model_list(data_dir / "presets.json", PresetDefinition),
    )
    validate_content_bundle(bundle)
    return bundle
