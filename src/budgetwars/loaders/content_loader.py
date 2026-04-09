from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping
from typing import TypeVar

from pydantic import BaseModel, TypeAdapter

from budgetwars.models import (
    AppConfig,
    CareerTrackDefinition,
    CityDefinition,
    ContentBundle,
    ConsequenceMatrixDefinition,
    DifficultyModifier,
    EducationProgramDefinition,
    EventDefinition,
    FocusActionDefinition,
    HousingOptionDefinition,
    PresetDefinition,
    ScoringWeights,
    TransportOptionDefinition,
    WealthStrategyDefinition,
    WinStateDefinition,
)
from budgetwars.models.content import LearnTopicDefinition

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


def load_content_bundle(data_dir: Path | None = None, *, content_files: Mapping[str, Path] | None = None) -> ContentBundle:
    if content_files is None:
        if data_dir is None:
            raise ValueError("load_content_bundle requires either data_dir or content_files.")
        content_files = {
            "config.json": data_dir / "config.json",
            "balance/difficulty_modifiers.json": data_dir / "balance" / "difficulty_modifiers.json",
            "balance/scoring_weights.json": data_dir / "balance" / "scoring_weights.json",
            "cities.json": data_dir / "cities.json",
            "careers.json": data_dir / "careers.json",
            "education.json": data_dir / "education.json",
            "housing.json": data_dir / "housing.json",
            "transport.json": data_dir / "transport.json",
            "focus_actions.json": data_dir / "focus_actions.json",
            "wealth_strategies.json": data_dir / "wealth_strategies.json",
            "events.json": data_dir / "events.json",
            "win_states.json": data_dir / "win_states.json",
            "learn_topics.json": data_dir / "learn_topics.json",
            "consequence_matrix.json": data_dir / "consequence_matrix.json",
            "presets.json": data_dir / "presets.json",
        }
    bundle = ContentBundle(
        config=_load_model(content_files["config.json"], AppConfig),
        difficulties=_load_model_list(content_files["balance/difficulty_modifiers.json"], DifficultyModifier),
        scoring_weights=_load_model(content_files["balance/scoring_weights.json"], ScoringWeights),
        cities=_load_model_list(content_files["cities.json"], CityDefinition),
        careers=_load_model_list(content_files["careers.json"], CareerTrackDefinition),
        education_programs=_load_model_list(content_files["education.json"], EducationProgramDefinition),
        housing_options=_load_model_list(content_files["housing.json"], HousingOptionDefinition),
        transport_options=_load_model_list(content_files["transport.json"], TransportOptionDefinition),
        focus_actions=_load_model_list(content_files["focus_actions.json"], FocusActionDefinition),
        wealth_strategies=_load_model_list(content_files["wealth_strategies.json"], WealthStrategyDefinition),
        events=_load_model_list(content_files["events.json"], EventDefinition),
        win_states=_load_model_list(content_files["win_states.json"], WinStateDefinition),
        learn_topics=_load_model_list(content_files["learn_topics.json"], LearnTopicDefinition),
        consequence_matrix=_load_model(content_files["consequence_matrix.json"], ConsequenceMatrixDefinition),
        presets=_load_model_list(content_files["presets.json"], PresetDefinition),
    )
    validate_content_bundle(bundle)
    return bundle
