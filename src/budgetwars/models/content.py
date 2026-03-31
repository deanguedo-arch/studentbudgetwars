from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .core import AppConfig, DifficultyModifier, ExamWeekDefinition, PriceCurveConfig


PlayerEffectMap = dict[str, float]


class CommodityDefinition(BaseModel):
    id: str
    name: str
    description: str
    min_price: int = Field(gt=0)
    max_price: int = Field(gt=0)
    typical_low: int = Field(gt=0)
    typical_high: int = Field(gt=0)
    volatility: float = Field(gt=0)
    size: int = Field(gt=0)
    district_biases: dict[str, float] = Field(default_factory=dict)
    rare_event_tags: list[str] = Field(default_factory=list)


class DistrictDefinition(BaseModel):
    id: str
    name: str
    description: str
    travel_cost: int = Field(ge=0)
    travel_energy_cost: int = Field(ge=0)
    travel_stress_delta: int = 0
    local_risk: int = Field(ge=0)
    event_tags: list[str] = Field(default_factory=list)
    commodity_biases: dict[str, float] = Field(default_factory=dict)
    service_ids: list[str] = Field(default_factory=list)
    gig_ids: list[str] = Field(default_factory=list)


class GigDefinition(BaseModel):
    id: str
    name: str
    description: str
    district_ids: list[str]
    pay: int = Field(gt=0)
    energy_cost: int = Field(ge=0)
    stress_delta: int = 0
    heat_delta: int = 0
    min_gpa: float = Field(ge=0, le=4.0, default=0)
    required_item_ids: list[str] = Field(default_factory=list)
    weight: int = Field(gt=0, default=1)


class ServiceDefinition(BaseModel):
    id: str
    name: str
    kind: Literal["bank", "supply_shop"]
    district_ids: list[str]
    item_ids: list[str] = Field(default_factory=list)
    loan_available: bool = False


class ItemDefinition(BaseModel):
    id: str
    name: str
    description: str
    price: int = Field(gt=0)
    size: int = Field(gt=0, default=1)
    district_ids: list[str] = Field(default_factory=list)
    use_effects: PlayerEffectMap = Field(default_factory=dict)


class EventDefinition(BaseModel):
    id: str
    name: str
    description: str
    trigger: Literal["weekly", "daily", "any"]
    weight: int = Field(gt=0)
    duration_days: int = Field(ge=0, default=0)
    event_tags: list[str] = Field(default_factory=list)
    commodity_multipliers: dict[str, float] = Field(default_factory=dict)
    district_commodity_multipliers: dict[str, dict[str, float]] = Field(default_factory=dict)
    stat_effects: PlayerEffectMap = Field(default_factory=dict)
    log_entry: str | None = None


class PresetDefinition(BaseModel):
    id: str
    name: str
    description: str
    starting_cash: int = Field(ge=0)
    starting_debt: int = Field(ge=0)
    starting_bank_balance: int = Field(ge=0)
    starting_energy: int = Field(gt=0)
    starting_stress: int = Field(ge=0)
    starting_heat: int = Field(ge=0)
    starting_gpa: float = Field(ge=0, le=4.0)
    starting_backpack_capacity: int = Field(gt=0)
    starting_district_id: str
    starting_item_ids: dict[str, int] = Field(default_factory=dict)


class ContentBundle(BaseModel):
    config: AppConfig
    difficulties: list[DifficultyModifier]
    price_curves: PriceCurveConfig
    exam_weeks: list[ExamWeekDefinition]
    districts: list[DistrictDefinition]
    commodities: list[CommodityDefinition]
    gigs: list[GigDefinition]
    events: list[EventDefinition]
    items: list[ItemDefinition]
    services: list[ServiceDefinition]
    presets: list[PresetDefinition]
