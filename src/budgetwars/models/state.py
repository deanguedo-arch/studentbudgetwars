from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, computed_field, field_validator

from .content import EventDefinition


StatEffects = dict[str, float]


class HousingState(BaseModel):
    option_id: str
    months_in_place: int = Field(ge=0, default=0)
    missed_payment_streak: int = Field(ge=0, default=0)
    lease_months_remaining: int = Field(ge=0, default=0)
    base_rent_multiplier: float = Field(ge=1.0, default=1.0)
    original_quality: int | None = None
    move_pressure: int = Field(ge=0, default=0)
    housing_stability: int = Field(ge=0, le=100, default=60)
    recent_move_penalty_months: int = Field(ge=0, default=0)
    layout_escalator: float = Field(ge=0.0, default=0.0)


class TransportState(BaseModel):
    option_id: str
    months_owned: int = Field(ge=0, default=0)
    breakdown_pressure: int = Field(ge=0, default=0)
    reliability_score: int = Field(ge=0, le=100, default=70)
    recent_repair_flag: bool = False
    recent_switch_penalty_months: int = Field(ge=0, default=0)
    vehicle_mileage: int = Field(ge=0, default=0)
    breakdown_escalator: float = Field(ge=1.0, default=1.0)


class CareerState(BaseModel):
    track_id: str
    branch_id: str | None = None
    tier_index: int = Field(ge=0, default=0)
    months_in_track: int = Field(ge=0, default=0)
    promotion_progress: int = Field(ge=0, default=0)
    layoff_pressure: int = Field(ge=0, default=0)
    promotion_momentum: int = Field(ge=0, le=100, default=45)
    transition_penalty_months: int = Field(ge=0, default=0)
    recent_performance_tag: str = "steady"
    months_at_tier: int = Field(ge=0, default=0)
    best_performance_streak: int = Field(ge=0, default=0)


class EducationState(BaseModel):
    program_id: str
    is_active: bool = False
    is_paused: bool = False
    months_completed: int = Field(ge=0, default=0)
    standing: int = Field(ge=0, le=100, default=70)
    college_gpa: float = Field(ge=0.0, le=4.0, default=2.5)
    training_passed: bool = False
    failure_streak: int = Field(ge=0, default=0)
    completed_program_ids: list[str] = Field(default_factory=list)
    earned_credential_ids: list[str] = Field(default_factory=list)
    reentry_drag_months: int = Field(ge=0, default=0)
    education_momentum: int = Field(ge=0, le=100, default=45)
    intensity_level: str = "standard"
    graduation_tier: str | None = None
    exam_stress_active: bool = False


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


class AnnualMilestoneSummary(BaseModel):
    year: int = Field(gt=0)
    age: int = Field(gt=0)
    net_worth: int
    monthly_income: int
    monthly_expenses: int
    monthly_surplus: int
    debt: int = Field(ge=0)
    housing_id: str
    career_track_id: str
    career_tier_label: str
    education_program_id: str
    stress: int = Field(ge=0)
    life_satisfaction: int = Field(ge=0)
    summary_lines: list[str] = Field(default_factory=list)


class LiveScoreSnapshot(BaseModel):
    projected_score: float
    score_tier: str
    biggest_risk: str
    breakdown: dict[str, float]


class PendingEvent(BaseModel):
    event_id: str
    months_remaining: int = Field(ge=0)
    source_event_id: str


class PlayerState(BaseModel):
    name: str
    cash: int
    savings: int
    high_interest_savings: int = 0
    index_fund: int = 0
    aggressive_growth_fund: int = 0
    debt: int
    monthly_income: int = 0
    monthly_expenses: int = 0
    monthly_surplus: int = 0
    stress: int = Field(ge=0)
    energy: int = Field(ge=0)
    life_satisfaction: int = Field(ge=0)
    family_support: int = Field(ge=0)
    social_stability: int = Field(ge=0)
    academic_strength: int = Field(ge=0, le=100)
    current_city_id: str
    budget_stance_id: str
    wealth_strategy_id: str
    opening_path_id: str
    selected_focus_action_id: str
    wealth_milestones_hit: list[str] = Field(default_factory=list)
    persistent_tags: list[str] = Field(default_factory=list)
    consecutive_correction_months: int = 0
    emergency_liquidation_count: int = 0
    credit_score: int = Field(ge=300, le=850, default=650)
    last_social_lifeline_year: int = 0
    career: CareerState
    education: EducationState
    housing: HousingState
    transport: TransportState

    @property
    def housing_id(self) -> str:
        return self.housing.option_id

    @housing_id.setter
    def housing_id(self, value: str) -> None:
        self.housing.option_id = value

    @property
    def transport_id(self) -> str:
        return self.transport.option_id

    @transport_id.setter
    def transport_id(self, value: str) -> None:
        self.transport.option_id = value


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
    max_social_stability: int = Field(gt=0)
    debt_game_over_threshold: int = Field(gt=0)
    burnout_stress_threshold: int = Field(gt=0)
    burnout_energy_threshold: int = Field(ge=0)
    burnout_streak_limit: int = Field(gt=0)
    housing_miss_limit: int = Field(gt=0)
    minimum_parent_fallback_support: int = Field(ge=0)
    academic_failure_streak_limit: int = Field(gt=0)
    current_market_regime_id: str
    player: PlayerState
    active_modifiers: list[ActiveMonthlyModifier] = Field(default_factory=list)
    pending_events: list[PendingEvent] = Field(default_factory=list)
    pending_user_choice_event_id: str | None = None
    pending_user_choice_event: EventDefinition | None = None
    pending_promotion_branch_track_id: str | None = None
    victory_state_id: str | None = None
    burnout_streak: int = Field(ge=0, default=0)
    log_messages: list[str] = Field(default_factory=list)
    recent_summary: list[str] = Field(default_factory=list)
    month_driver_notes: list[str] = Field(default_factory=list)
    annual_milestones: list[AnnualMilestoneSummary] = Field(default_factory=list)
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
    run_identity: str | None = None
    breakdown: dict[str, float]


class SaveGamePayload(BaseModel):
    version: int = 9
    state: GameState


class FileSystemPaths(BaseModel):
    root: Path
    data_dir: Path
    saves_dir: Path
