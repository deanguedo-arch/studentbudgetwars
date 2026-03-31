from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


StatEffects = dict[str, int]
ExpenseCadence = Literal["weekly", "monthly", "one_time"]


class DifficultyDefinition(BaseModel):
    id: str
    name: str
    description: str
    income_multiplier: float = Field(gt=0)
    expense_multiplier: float = Field(gt=0)
    stress_multiplier: float = Field(gt=0)
    starting_cash_bonus: int = 0


class GameConfig(BaseModel):
    game_title: str
    term_weeks: int = Field(gt=0)
    starting_week: int = Field(ge=1)
    default_seed: int
    max_stress: int = Field(gt=0)
    max_energy: int = Field(gt=0)
    message_log_limit: int = Field(gt=0)
    starting_location_id: str
    weekly_event_chance: float = Field(ge=0, le=1)
    low_energy_threshold: int = Field(ge=0)
    low_energy_week_limit: int = Field(gt=0)
    debt_game_over_threshold: int = Field(gt=0)
    max_missed_essential_weeks: int = Field(gt=0)
    debt_interest_rate: float = Field(ge=0)
    overdraft_fee: int = Field(ge=0)
    autosave_name: str
    difficulties: list[DifficultyDefinition]


class ItemDefinition(BaseModel):
    id: str
    name: str
    category: str
    price: int = Field(gt=0)
    description: str
    effects: StatEffects = Field(default_factory=dict)


class ExpenseDefinition(BaseModel):
    id: str
    name: str
    amount: int = Field(gt=0)
    cadence: ExpenseCadence
    mandatory: bool
    description: str


class JobDefinition(BaseModel):
    id: str
    name: str
    hourly_pay: int = Field(gt=0)
    hours_per_week: int = Field(ge=0)
    energy_cost: int = Field(ge=0)
    stress_delta: int
    location_id: str
    description: str


class LocationDefinition(BaseModel):
    id: str
    name: str
    description: str
    modifiers: StatEffects = Field(default_factory=dict)


class EventChoiceDefinition(BaseModel):
    id: str
    label: str
    description: str
    effects: StatEffects = Field(default_factory=dict)


class EventDefinition(BaseModel):
    id: str
    name: str
    description: str
    weight: int = Field(gt=0)
    effects: StatEffects = Field(default_factory=dict)
    choices: list[EventChoiceDefinition] = Field(default_factory=list)


class PresetDefinition(BaseModel):
    id: str
    name: str
    description: str
    starting_cash: int = Field(ge=0)
    starting_savings: int = Field(ge=0)
    starting_debt: int = Field(ge=0)
    starting_stress: int = Field(ge=0)
    starting_energy: int = Field(gt=0)
    starting_location_id: str
    starting_job_id: str


class ScoringDefinition(BaseModel):
    cash_weight: float
    savings_weight: float
    debt_weight: float
    stress_weight: float
    energy_weight: float
    survival_bonus: float
    failure_floor: float


class PlayerState(BaseModel):
    name: str
    cash: int
    savings: int
    debt: int
    stress: int = Field(ge=0)
    energy: int = Field(ge=0)
    location_id: str
    job_id: str | None = None
    inventory: dict[str, int] = Field(default_factory=dict)


class GameState(BaseModel):
    game_title: str
    difficulty_id: str
    current_week: int = Field(ge=1)
    term_weeks: int = Field(gt=0)
    max_stress: int = Field(gt=0)
    max_energy: int = Field(gt=0)
    low_energy_threshold: int = Field(ge=0)
    low_energy_week_limit: int = Field(gt=0)
    debt_game_over_threshold: int = Field(gt=0)
    max_missed_essential_weeks: int = Field(gt=0)
    seed: int
    player: PlayerState
    consecutive_low_energy_weeks: int = Field(ge=0, default=0)
    missed_essential_weeks: int = Field(ge=0, default=0)
    game_over_reason: str | None = None
    message_log: list[str] = Field(default_factory=list)
    active_event_ids: list[str] = Field(default_factory=list)

    @field_validator("message_log")
    @classmethod
    def strip_empty_messages(cls, value: list[str]) -> list[str]:
        return [message for message in value if message.strip()]


class ContentBundle(BaseModel):
    config: GameConfig
    items: list[ItemDefinition]
    expenses: list[ExpenseDefinition]
    jobs: list[JobDefinition]
    locations: list[LocationDefinition]
    events: list[EventDefinition]
    presets: list[PresetDefinition]
    scoring: ScoringDefinition


class FinalScoreSummary(BaseModel):
    final_score: float
    survived_term: bool
    outcome: str
    breakdown: dict[str, float]


class SaveGamePayload(BaseModel):
    version: int = 1
    state: GameState


class FileSystemPaths(BaseModel):
    root: Path
    data_dir: Path
    saves_dir: Path
