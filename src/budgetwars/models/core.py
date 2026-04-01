from __future__ import annotations

from pydantic import BaseModel, Field


class BudgetStanceDefinition(BaseModel):
    id: str
    name: str
    description: str
    discretionary_spending: int = Field(ge=0)
    debt_payment_multiplier: float = Field(ge=0)
    savings_contribution_rate: float = Field(ge=0, le=1)
    stress_delta: int = 0
    life_satisfaction_delta: int = 0


class OpeningPathDefinition(BaseModel):
    id: str
    name: str
    description: str
    starting_career_track_id: str
    starting_education_program_id: str
    starting_housing_id: str
    starting_transport_id: str
    starting_budget_stance_id: str
    cash_delta: int = 0
    debt_delta: int = 0
    stress_delta: int = 0
    life_satisfaction_delta: int = 0
    family_support_delta: int = 0


class AppConfig(BaseModel):
    game_title: str
    total_months: int = Field(gt=0)
    start_age: int = Field(gt=0)
    default_seed: int
    autosave_name: str
    message_log_limit: int = Field(gt=0)
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
    base_living_cost: int = Field(gt=0)
    minimum_debt_payment: int = Field(gt=0)
    debt_payment_rate: float = Field(gt=0)
    debt_interest_rate: float = Field(ge=0)
    savings_growth_rate: float = Field(ge=0)
    primary_event_chance: float = Field(ge=0, le=1)
    secondary_event_chance: float = Field(ge=0, le=1)
    parent_drift_family_penalty: int = Field(ge=0)
    parent_drift_satisfaction_penalty: int = Field(ge=0)
    baseline_monthly_energy_recovery: int = Field(ge=0)
    baseline_monthly_stress_relief: int = Field(ge=0)
    budget_stances: list[BudgetStanceDefinition]
    opening_paths: list[OpeningPathDefinition]

    @property
    def total_years(self) -> int:
        return self.total_months // 12


class DifficultyModifier(BaseModel):
    id: str
    name: str
    description: str
    cash_bonus: int = 0
    debt_bonus: int = 0
    income_multiplier: float = Field(gt=0)
    housing_cost_multiplier: float = Field(gt=0)
    transport_cost_multiplier: float = Field(gt=0)
    stress_multiplier: float = Field(gt=0)
    progress_multiplier: float = Field(gt=0)
    interest_multiplier: float = Field(gt=0)


class ScoringWeights(BaseModel):
    financial_position: float = Field(ge=0)
    career_and_credentials: float = Field(ge=0)
    housing_stability: float = Field(ge=0)
    debt_burden: float = Field(ge=0)
    wellbeing: float = Field(ge=0)
