from __future__ import annotations

from pydantic import BaseModel, Field

from .core import AppConfig, DifficultyModifier, ScoringWeights


StatEffects = dict[str, float]


class CityDefinition(BaseModel):
    id: str
    name: str
    description: str
    housing_cost_multiplier: float = Field(gt=0)
    living_cost_multiplier: float = Field(gt=0)
    transport_cost_multiplier: float = Field(gt=0)
    education_cost_multiplier: float = Field(gt=0, default=1.0)
    family_support_bonus: int = 0
    opportunity_text: str
    pressure_text: str
    career_income_biases: dict[str, float] = Field(default_factory=dict)


class CareerTierDefinition(BaseModel):
    label: str
    monthly_income: int = Field(gt=0)
    energy_delta: int
    stress_delta: int
    life_satisfaction_delta: int = 0
    social_stability_delta: int = 0
    promotion_target: int = Field(gt=0)
    required_credential_ids: list[str] = Field(default_factory=list)
    required_minimum_gpa: float | None = Field(default=None, ge=0.0, le=4.0)
    required_pass_state: bool = False
    seniority_income_bonus: int = 0


class CareerTrackDefinition(BaseModel):
    id: str
    name: str
    description: str
    entry_path_ids: list[str] = Field(default_factory=list)
    minimum_transport_access: int = Field(ge=0)
    entry_required_credential_ids: list[str] = Field(default_factory=list)
    entry_required_education_program_id: str | None = None
    entry_requires_active_education: bool = False
    entry_minimum_gpa: float | None = Field(default=None, ge=0.0, le=4.0)
    entry_requires_pass_state: bool = False
    income_variance: float = Field(ge=0, le=0.5, default=0.0)
    social_income_factor: float = Field(ge=0, le=0.05, default=0.0)
    layoff_weight: float = Field(ge=0.1, default=1.0)
    promotion_weight: float = Field(ge=0.1, default=1.0)
    stability_profile: int = Field(ge=0, le=100, default=50)
    volatility_profile: int = Field(ge=0, le=100, default=50)
    transport_sensitivity: int = Field(ge=0, le=100, default=50)
    city_sensitivity: int = Field(ge=0, le=100, default=50)
    skill_transfer_map: dict[str, float] = Field(default_factory=dict)
    tiers: list[CareerTierDefinition]


class EducationProgramDefinition(BaseModel):
    id: str
    name: str
    description: str
    monthly_cost: int = Field(ge=0)
    monthly_stress: int = 0
    monthly_energy_delta: int = 0
    duration_months: int = Field(ge=0)
    credential_id: str | None = None
    entry_path_ids: list[str] = Field(default_factory=list)
    completion_life_satisfaction_bonus: int = 0
    applicable_career_ids: list[str] = Field(default_factory=list)
    uses_gpa: bool = False
    pass_state_program: bool = False
    can_pause: bool = True
    minimum_academic_strength: int = Field(ge=0, le=100, default=0)


class HousingOptionDefinition(BaseModel):
    id: str
    name: str
    description: str
    base_monthly_cost: int = Field(ge=0)
    move_in_cost: int = Field(ge=0)
    stress_delta: int = 0
    life_satisfaction_delta: int = 0
    social_stability_delta: int = 0
    roommate_event_weight: float = Field(ge=0)
    quality_score: int = Field(ge=0, le=100)
    flexibility_score: int = Field(ge=0, le=100, default=50)
    recovery_score: int = Field(ge=0, le=100, default=50)
    study_compatibility: int = Field(ge=0, le=100, default=50)
    requires_hometown: bool = False
    minimum_family_support: int = Field(ge=0, default=0)
    student_only: bool = False
    minimum_credit_score: int = Field(ge=0, default=0)


class TransportOptionDefinition(BaseModel):
    id: str
    name: str
    description: str
    upfront_cost: int = Field(ge=0)
    monthly_payment: int = Field(ge=0)
    insurance_cost: int = Field(ge=0)
    fuel_maintenance_cost: int = Field(ge=0)
    commute_stress_delta: int = 0
    commute_time_modifier: int = 0
    access_level: int = Field(ge=0)
    reliability: float = Field(ge=0, le=1)
    breakdown_risk: float = Field(ge=0, le=1, default=0.0)
    repair_event_weight: float = Field(ge=0)
    odd_hour_access: int = Field(ge=0, le=100, default=50)
    liquidity_pressure: int = Field(ge=0, le=100, default=50)
    quality_score: int = Field(ge=0, le=100)
    minimum_credit_score: int = Field(ge=0, default=0)


class FocusActionDefinition(BaseModel):
    id: str
    name: str
    description: str
    income_multiplier: float = Field(gt=0)
    promotion_progress_bonus: int = 0
    education_progress_bonus: int = 0
    stress_delta: int = 0
    energy_delta: int = 0
    life_satisfaction_delta: int = 0
    social_stability_delta: int = 0
    stat_effects: StatEffects = Field(default_factory=dict)


class WealthStrategyDefinition(BaseModel):
    id: str
    name: str
    description: str
    emergency_cash_floor: int = Field(ge=0, default=150)
    safe_savings_rate: float = Field(ge=0, le=1, default=0.0)
    index_invest_rate: float = Field(ge=0, le=1, default=0.0)
    growth_invest_rate: float = Field(ge=0, le=1, default=0.0)
    extra_debt_payment_rate: float = Field(ge=0, le=1, default=0.0)
    liquidity_bias: int = Field(ge=0, le=100, default=50)
    risk_bias: int = Field(ge=0, le=100, default=50)
    rebalance_trigger: str | None = None


class ModifierTemplate(BaseModel):
    id: str
    label: str
    duration_months: int = Field(gt=0)
    stat_effects: StatEffects = Field(default_factory=dict)
    income_multiplier: float = Field(gt=0, default=1.0)
    housing_cost_delta: int = 0
    living_cost_delta: int = 0
    transport_cost_delta: int = 0
    education_cost_delta: int = 0
    promotion_progress_delta: int = 0
    education_progress_delta: int = 0
    transport_switch_discount: int = 0


class EventChoice(BaseModel):
    id: str
    label: str
    description: str
    stat_effects: StatEffects = Field(default_factory=dict)


class EventDefinition(BaseModel):
    id: str
    name: str
    description: str
    weight: int = Field(gt=0)
    min_month: int = Field(ge=1, default=1)
    eligible_city_ids: list[str] = Field(default_factory=list)
    eligible_housing_ids: list[str] = Field(default_factory=list)
    eligible_transport_ids: list[str] = Field(default_factory=list)
    eligible_career_ids: list[str] = Field(default_factory=list)
    eligible_education_ids: list[str] = Field(default_factory=list)
    eligible_opening_path_ids: list[str] = Field(default_factory=list)
    eligible_modifier_ids: list[str] = Field(default_factory=list)
    minimum_stress: int | None = Field(default=None, ge=0)
    minimum_debt: int | None = Field(default=None, ge=0)
    minimum_family_support: int | None = Field(default=None, ge=0)
    maximum_family_support: int | None = Field(default=None, ge=0)
    minimum_social_stability: int | None = Field(default=None, ge=0)
    maximum_social_stability: int | None = Field(default=None, ge=0)
    maximum_transport_reliability: int | None = Field(default=None, ge=0, le=100)
    maximum_housing_stability: int | None = Field(default=None, ge=0, le=100)
    maximum_life_satisfaction: int | None = Field(default=None, ge=0, le=100)
    minimum_credit_score: int | None = Field(default=None, ge=300, le=850)
    maximum_credit_score: int | None = Field(default=None, ge=300, le=850)
    eligible_market_regime_ids: list[str] = Field(default_factory=list)
    immediate_effects: StatEffects = Field(default_factory=dict)
    choices: list[EventChoice] = Field(default_factory=list)
    modifier: ModifierTemplate | None = None
    log_entry: str | None = None
    chained_event_id: str | None = None
    chained_delay_months: int = Field(ge=0, default=1)


class WinStateDefinition(BaseModel):
    id: str
    name: str
    description: str
    ending_label: str
    minimum_score: float = Field(ge=0, default=0.0)
    minimum_cash: int = Field(ge=0, default=0)
    minimum_savings: int = Field(ge=0, default=0)
    minimum_net_worth: int = Field(default=0)
    maximum_debt: int | None = Field(default=None, ge=0)
    minimum_career_tier_index: int = Field(ge=0, default=0)
    minimum_career_track_ids: list[str] = Field(default_factory=list)
    score_multiplier: float = Field(gt=0, default=1.0)


class LearnTopicDefinition(BaseModel):
    id: str
    title: str
    what_it_is: str
    how_to_raise: list[str] = Field(default_factory=list)
    how_to_lower: list[str] = Field(default_factory=list)
    why_it_matters: list[str] = Field(default_factory=list)


class PresetDefinition(BaseModel):
    id: str
    name: str
    description: str
    starting_cash: int = Field(ge=0)
    starting_savings: int = Field(ge=0)
    starting_debt: int = Field(ge=0)
    starting_stress: int = Field(ge=0)
    starting_energy: int = Field(gt=0)
    starting_life_satisfaction: int = Field(ge=0)
    starting_family_support: int = Field(ge=0)
    starting_social_stability: int = Field(ge=0, le=100, default=50)
    academic_strength: int = Field(ge=0, le=100)


class ContentBundle(BaseModel):
    config: AppConfig
    difficulties: list[DifficultyModifier]
    scoring_weights: ScoringWeights
    cities: list[CityDefinition]
    careers: list[CareerTrackDefinition]
    education_programs: list[EducationProgramDefinition]
    housing_options: list[HousingOptionDefinition]
    transport_options: list[TransportOptionDefinition]
    focus_actions: list[FocusActionDefinition]
    wealth_strategies: list[WealthStrategyDefinition]
    events: list[EventDefinition]
    win_states: list[WinStateDefinition]
    learn_topics: list[LearnTopicDefinition]
    presets: list[PresetDefinition]
