from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, computed_field, field_validator


StatEffects = dict[str, float]


class CareerState(BaseModel):
    track_id: str
    tier_index: int = Field(ge=0, default=0)
    months_in_track: int = Field(ge=0, default=0)
    promotion_progress: int = Field(ge=0, default=0)


class EducationState(BaseModel):
    program_id: str
    is_active: bool = False
    months_completed: int = Field(ge=0, default=0)
    standing: int = Field(ge=0, le=100, default=70)
    college_gpa: float = Field(ge=0.0, le=4.0, default=2.5)
    completed_program_ids: list[str] = Field(default_factory=list)
    earned_credential_ids: list[str] = Field(default_factory=list)


class ActiveMonthlyModifier(BaseModel):
    id: str
    label: str
    remaining_months: int = Field(gt=0)
    stat_effects: StatEffects = Field(default_factory=dict)
    income_multiplier: float = Field(gt=0, default=1.0)
    housing_cost_delta: int = 0
    living_cost_delta: int = 0
    transport_cost_delta: int = 0
    education_cost_delta: int = 0
    promotion_progress_delta: int = 0
    education_progress_delta: int = 0
    transport_switch_discount: int = 0


class PlayerState(BaseModel):
    name: str
    cash: int
    savings: int
    debt: int
    monthly_surplus: int = 0
    stress: int = Field(ge=0)
    energy: int = Field(ge=0)
    life_satisfaction: int = Field(ge=0)
    family_support: int = Field(ge=0)
    academic_strength: int = Field(ge=0, le=100)
    current_city_id: str
    housing_id: str
    transport_id: str
    budget_stance_id: str
    opening_path_id: str
    selected_focus_action_id: str
    career: CareerState
    education: EducationState


class GameState(BaseModel):
    game_title: str
    player_name: str
    difficulty_id: str
    seed: int
    start_age: int = Field(gt=0)
    current_month: int = Field(ge=1)
    total_months: int = Field(gt=0)
    max_stress: int = Field(gt=0)
    max_energy: int = Field(gt=0)
    max_life_satisfaction: int = Field(gt=0)
    max_family_support: int = Field(gt=0)
    debt_game_over_threshold: int = Field(gt=0)
    burnout_stress_threshold: int = Field(gt=0)
    burnout_energy_threshold: int = Field(ge=0)
    burnout_streak_limit: int = Field(gt=0)
    housing_miss_limit: int = Field(gt=0)
    minimum_parent_fallback_support: int = Field(ge=0)
    player: PlayerState
    active_modifiers: list[ActiveMonthlyModifier] = Field(default_factory=list)
    missed_housing_payments: int = Field(ge=0, default=0)
    burnout_streak: int = Field(ge=0, default=0)
    log_messages: list[str] = Field(default_factory=list)
    recent_summary: list[str] = Field(default_factory=list)
    game_over_reason: str | None = None

    @computed_field
    @property
    def current_year(self) -> int:
        return ((self.current_month - 1) // 12) + 1

    @computed_field
    @property
    def current_age(self) -> int:
        return self.start_age + ((self.current_month - 1) // 12)

    @computed_field
    @property
    def months_left(self) -> int:
        return max(0, self.total_months - self.current_month + 1)

    @field_validator("log_messages")
    @classmethod
    def strip_empty_messages(cls, value: list[str]) -> list[str]:
        return [message for message in value if message.strip()]


class FinalScoreSummary(BaseModel):
    final_score: float
    survived_to_28: bool
    outcome: str
    ending_label: str
    breakdown: dict[str, float]


class SaveGamePayload(BaseModel):
    version: int = 4
    state: GameState


class FileSystemPaths(BaseModel):
    root: Path
    data_dir: Path
    saves_dir: Path
