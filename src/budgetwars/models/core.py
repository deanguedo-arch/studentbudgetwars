from __future__ import annotations

from pydantic import BaseModel, Field


class WeeklyCostDefinition(BaseModel):
    housing: int = Field(ge=0)
    utilities: int = Field(ge=0)
    phone: int = Field(ge=0)

    @property
    def total(self) -> int:
        return self.housing + self.utilities + self.phone


class AppConfig(BaseModel):
    game_title: str
    days_per_week: int = Field(gt=0)
    term_weeks: int = Field(gt=0)
    max_stress: int = Field(gt=0)
    max_energy: int = Field(gt=0)
    max_heat: int = Field(gt=0)
    low_energy_threshold: int = Field(ge=0)
    low_energy_streak_limit: int = Field(gt=0)
    debt_game_over_threshold: int = Field(gt=0)
    minimum_survival_gpa: float = Field(ge=0)
    minimum_survival_net_worth: int
    default_seed: int
    autosave_name: str
    message_log_limit: int = Field(gt=0)
    starting_bank_balance: int
    starting_backpack_capacity: int = Field(gt=0)
    weekly_costs: WeeklyCostDefinition
    debt_interest_rate: float = Field(ge=0)
    bank_interest_rate: float = Field(ge=0)
    heat_decay_per_week: int = Field(ge=0)
    daily_event_chance: float = Field(ge=0, le=1)
    loan_limit: int = Field(gt=0)
    rest_energy_gain: int = Field(gt=0)
    rest_stress_reduction: int = Field(gt=0)
    study_energy_cost: int = Field(gt=0)
    study_stress_delta: int
    study_points_per_action: int = Field(gt=0)
    gig_heat_threshold: int = Field(ge=0)
    weekly_market_event_count: int = Field(gt=0)

    @property
    def total_days(self) -> int:
        return self.days_per_week * self.term_weeks


class DifficultyModifier(BaseModel):
    id: str
    name: str
    description: str
    cash_bonus: int = 0
    debt_bonus: int = 0
    rent_multiplier: float = Field(gt=0)
    debt_interest_multiplier: float = Field(gt=0)
    price_spread_multiplier: float = Field(gt=0)
    study_requirement_multiplier: float = Field(gt=0)
    energy_recovery_multiplier: float = Field(gt=0)
    stress_multiplier: float = Field(gt=0)


class PriceCurveConfig(BaseModel):
    base_randomness_floor: float = Field(gt=0)
    base_randomness_ceiling: float = Field(gt=0)
    scarcity_multiplier_floor: float = Field(gt=0)
    scarcity_multiplier_ceiling: float = Field(gt=0)
    flood_multiplier_floor: float = Field(gt=0)
    flood_multiplier_ceiling: float = Field(gt=0)


class ExamWeekDefinition(BaseModel):
    week: int = Field(gt=0)
    label: str
    required_study_points: int = Field(gt=0)
    gpa_penalty: float = Field(ge=0)
    gpa_reward: float = Field(ge=0)
    stress_delta: int
