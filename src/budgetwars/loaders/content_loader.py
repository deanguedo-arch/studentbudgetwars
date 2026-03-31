from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, TypeAdapter

from budgetwars.models import (
    AppConfig,
    CommodityDefinition,
    ContentBundle,
    DifficultyModifier,
    DistrictDefinition,
    EventDefinition,
    ExamWeekDefinition,
    GigDefinition,
    ItemDefinition,
    PresetDefinition,
    PriceCurveConfig,
    ServiceDefinition,
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
        price_curves=_load_model(data_dir / "balance" / "price_curves.json", PriceCurveConfig),
        exam_weeks=_load_model_list(data_dir / "balance" / "exam_weeks.json", ExamWeekDefinition),
        districts=_load_model_list(data_dir / "districts.json", DistrictDefinition),
        commodities=_load_model_list(data_dir / "commodities.json", CommodityDefinition),
        gigs=_load_model_list(data_dir / "gigs.json", GigDefinition),
        events=_load_model_list(data_dir / "events.json", EventDefinition),
        items=_load_model_list(data_dir / "items.json", ItemDefinition),
        services=_load_model_list(data_dir / "services.json", ServiceDefinition),
        presets=_load_model_list(data_dir / "presets.json", PresetDefinition),
    )
    validate_content_bundle(bundle)
    return bundle
