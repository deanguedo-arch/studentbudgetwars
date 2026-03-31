from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, computed_field, field_validator


PlayerEffectMap = dict[str, float]


class InventoryEntry(BaseModel):
    commodity_id: str
    quantity: int = Field(gt=0)
    average_price: int = Field(ge=0)


class SupportItemEntry(BaseModel):
    item_id: str
    quantity: int = Field(gt=0)


class MarketSnapshot(BaseModel):
    district_id: str
    day_index: int = Field(gt=0)
    listings: dict[str, int] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class ActiveWorldEvent(BaseModel):
    event_id: str
    name: str
    description: str
    expires_on_day: int = Field(gt=0)
    commodity_multipliers: dict[str, float] = Field(default_factory=dict)
    district_commodity_multipliers: dict[str, dict[str, float]] = Field(default_factory=dict)
    stat_effects: PlayerEffectMap = Field(default_factory=dict)
    log_entry: str | None = None


class PlayerState(BaseModel):
    name: str
    cash: int
    debt: int
    bank_balance: int = 0
    energy: int = Field(ge=0)
    stress: int = Field(ge=0)
    heat: int = Field(ge=0)
    gpa: float = Field(ge=0, le=4.0)
    current_district_id: str
    backpack_capacity: int = Field(gt=0)
    commodity_inventory: list[InventoryEntry] = Field(default_factory=list)
    item_inventory: list[SupportItemEntry] = Field(default_factory=list)


class GameState(BaseModel):
    game_title: str
    player_name: str
    difficulty_id: str
    seed: int
    current_day: int = Field(ge=1)
    total_days: int = Field(gt=0)
    days_per_week: int = Field(gt=0)
    max_stress: int = Field(gt=0)
    max_energy: int = Field(gt=0)
    max_heat: int = Field(gt=0)
    low_energy_threshold: int = Field(ge=0)
    low_energy_streak_limit: int = Field(gt=0)
    debt_game_over_threshold: int = Field(gt=0)
    minimum_survival_gpa: float = Field(ge=0)
    minimum_survival_net_worth: int
    player: PlayerState
    current_markets: dict[str, MarketSnapshot] = Field(default_factory=dict)
    active_events: list[ActiveWorldEvent] = Field(default_factory=list)
    weekly_study_points: int = Field(ge=0, default=0)
    low_energy_streak: int = Field(ge=0, default=0)
    log_messages: list[str] = Field(default_factory=list)
    recent_summary: list[str] = Field(default_factory=list)
    game_over_reason: str | None = None

    @computed_field
    @property
    def current_week(self) -> int:
        return ((self.current_day - 1) // self.days_per_week) + 1

    @computed_field
    @property
    def days_left(self) -> int:
        return max(0, self.total_days - self.current_day + 1)

    @field_validator("log_messages")
    @classmethod
    def strip_empty_messages(cls, value: list[str]) -> list[str]:
        return [message for message in value if message.strip()]


class FinalScoreSummary(BaseModel):
    final_score: float
    survived_term: bool
    outcome: str
    breakdown: dict[str, float]


class SaveGamePayload(BaseModel):
    version: int = 2
    state: GameState


class FileSystemPaths(BaseModel):
    root: Path
    data_dir: Path
    saves_dir: Path
