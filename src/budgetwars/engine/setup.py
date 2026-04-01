from __future__ import annotations

from random import Random

from budgetwars.models import (
    CareerState,
    ContentBundle,
    EducationState,
    GameState,
    HousingState,
    PlayerState,
    TransportState,
)

from .effects import append_logs, clamp_player_state
from .lookups import (
    get_academic_level,
    get_budget_stance,
    get_city,
    get_difficulty,
    get_family_support_level,
    get_focus_action,
    get_housing_option,
    get_opening_path,
    get_preset,
    get_savings_band,
    get_transport_option,
)


def _starting_housing_id(bundle: ContentBundle, city_id: str, path_id: str, family_support: int) -> str:
    opening_path = get_opening_path(bundle, path_id)
    housing = get_housing_option(bundle, opening_path.starting_housing_id)
    if housing.requires_hometown and city_id != "hometown_low_cost":
        return "roommates"
    if family_support < housing.minimum_family_support:
        return "roommates"
    return housing.id


def build_new_game_state(
    bundle: ContentBundle,
    player_name: str,
    preset_id: str,
    difficulty_id: str,
    city_id: str,
    opening_path_id: str,
    academic_level_id: str,
    family_support_level_id: str,
    savings_band_id: str,
    seed: int,
) -> GameState:
    preset = get_preset(bundle, preset_id)
    difficulty = get_difficulty(bundle, difficulty_id)
    city = get_city(bundle, city_id)
    opening_path = get_opening_path(bundle, opening_path_id)
    academic_level = get_academic_level(bundle, academic_level_id)
    support_level = get_family_support_level(bundle, family_support_level_id)
    savings_band = get_savings_band(bundle, savings_band_id)
    _ = get_budget_stance(bundle, opening_path.starting_budget_stance_id)
    _ = get_focus_action(bundle, opening_path.starting_focus_action_id)

    academic_strength = max(
        0,
        min(
            100,
            preset.academic_strength + academic_level.academic_strength_delta + opening_path.academic_strength_delta,
        ),
    )
    family_support = (
        preset.starting_family_support
        + city.family_support_bonus
        + support_level.family_support_delta
        + opening_path.family_support_delta
    )
    housing_id = _starting_housing_id(bundle, city_id, opening_path_id, family_support)

    starting_cash = preset.starting_cash + opening_path.cash_delta + savings_band.cash_delta + difficulty.cash_bonus
    starting_savings = preset.starting_savings + opening_path.savings_delta + savings_band.savings_delta
    starting_debt = preset.starting_debt + opening_path.debt_delta + savings_band.debt_delta + difficulty.debt_bonus
    starting_stress = preset.starting_stress + opening_path.stress_delta + academic_level.stress_delta
    starting_life_satisfaction = (
        preset.starting_life_satisfaction
        + opening_path.life_satisfaction_delta
        + support_level.life_satisfaction_delta
        + savings_band.life_satisfaction_delta
    )
    starting_social = preset.starting_social_stability + support_level.social_stability_delta + opening_path.social_stability_delta
    starting_standing = max(35, min(100, 55 + ((academic_strength - 50) // 2) + academic_level.standing_delta + opening_path.standing_delta))
    starting_gpa = max(
        1.5,
        min(4.0, round(2.2 + ((academic_strength - 50) * 0.03) + academic_level.starting_gpa_delta + opening_path.starting_gpa_delta, 2)),
    )

    player = PlayerState(
        name=player_name,
        cash=max(0, starting_cash),
        savings=max(0, starting_savings),
        high_interest_savings=0,
        index_fund=0,
        aggressive_growth_fund=0,
        debt=max(0, starting_debt),
        monthly_income=0,
        monthly_expenses=0,
        monthly_surplus=0,
        stress=max(0, starting_stress),
        energy=preset.starting_energy,
        life_satisfaction=max(0, starting_life_satisfaction),
        family_support=max(0, family_support),
        social_stability=max(0, starting_social),
        academic_strength=academic_strength,
        current_city_id=city_id,
        budget_stance_id=opening_path.starting_budget_stance_id,
        opening_path_id=opening_path_id,
        selected_focus_action_id=opening_path.starting_focus_action_id,
        career=CareerState(track_id=opening_path.starting_career_track_id),
        education=EducationState(
            program_id=opening_path.starting_education_program_id,
            is_active=opening_path.starting_education_program_id != "none",
            standing=starting_standing,
            college_gpa=starting_gpa,
        ),
        housing=HousingState(option_id=housing_id),
        transport=TransportState(option_id=opening_path.starting_transport_id),
    )
    state = GameState(
        game_title=bundle.config.game_title,
        player_name=player_name,
        difficulty_id=difficulty_id,
        seed=seed,
        start_age=bundle.config.start_age,
        current_month=1,
        total_months=bundle.config.total_months,
        max_stress=bundle.config.max_stress,
        max_energy=bundle.config.max_energy,
        max_life_satisfaction=bundle.config.max_life_satisfaction,
        max_family_support=bundle.config.max_family_support,
        max_social_stability=bundle.config.max_social_stability,
        debt_game_over_threshold=bundle.config.debt_game_over_threshold,
        burnout_stress_threshold=bundle.config.burnout_stress_threshold,
        burnout_energy_threshold=bundle.config.burnout_energy_threshold,
        burnout_streak_limit=bundle.config.burnout_streak_limit,
        housing_miss_limit=bundle.config.housing_miss_limit,
        minimum_parent_fallback_support=bundle.config.minimum_parent_fallback_support,
        academic_failure_streak_limit=bundle.config.academic_failure_streak_limit,
        current_market_regime_id=bundle.config.default_market_regime_id,
        player=player,
    )
    starting_housing = get_housing_option(bundle, housing_id)
    starting_transport = get_transport_option(bundle, opening_path.starting_transport_id)
    state.player.housing.housing_stability = starting_housing.quality_score
    state.player.transport.reliability_score = int(round(starting_transport.reliability * 100))
    clamp_player_state(state)
    append_logs(
        state,
        [
            f"{player_name} just graduated at age {state.start_age}.",
            f"You start in {city.name} as a {preset.name.lower()} on the {opening_path.name.lower()} path.",
            (
                f"Setup: {housing_id.replace('_', ' ')}, {opening_path.starting_transport_id.replace('_', ' ')}, "
                f"{player.career.track_id.replace('_', ' ')}, {player.education.program_id.replace('_', ' ')}."
            ),
        ],
    )
    return state


def build_rng(seed: int | None, fallback_seed: int) -> Random:
    return Random(seed if seed is not None else fallback_seed)
