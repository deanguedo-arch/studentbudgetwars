from __future__ import annotations

from random import Random

from budgetwars.models import CareerState, ContentBundle, EducationState, GameState, PlayerState

from .effects import append_logs, clamp_player_state
from .lookups import (
    get_budget_stance,
    get_city,
    get_difficulty,
    get_focus_action,
    get_housing_option,
    get_opening_path,
    get_preset,
)


def _starting_housing_id(bundle: ContentBundle, city_id: str, path_id: str, family_support: int) -> str:
    opening_path = get_opening_path(bundle, path_id)
    housing = get_housing_option(bundle, opening_path.starting_housing_id)
    if housing.requires_hometown and city_id != "hometown":
        return "roommates"
    if family_support < housing.minimum_family_support:
        return "roommates"
    return housing.id


def _starting_focus_action_id(path_id: str) -> str:
    if path_id in {"college", "trades_apprenticeship"}:
        return "push_forward"
    return "stack_cash"


def build_new_game_state(
    bundle: ContentBundle,
    player_name: str,
    preset_id: str,
    difficulty_id: str,
    city_id: str,
    opening_path_id: str,
    seed: int,
) -> GameState:
    preset = get_preset(bundle, preset_id)
    difficulty = get_difficulty(bundle, difficulty_id)
    city = get_city(bundle, city_id)
    opening_path = get_opening_path(bundle, opening_path_id)
    _ = get_budget_stance(bundle, opening_path.starting_budget_stance_id)
    _ = get_focus_action(bundle, _starting_focus_action_id(opening_path_id))

    family_support = preset.starting_family_support + city.family_support_bonus + opening_path.family_support_delta
    housing_id = _starting_housing_id(bundle, city_id, opening_path_id, family_support)

    starting_cash = preset.starting_cash + opening_path.cash_delta + difficulty.cash_bonus
    starting_savings = preset.starting_savings
    starting_debt = preset.starting_debt + opening_path.debt_delta + difficulty.debt_bonus
    starting_stress = preset.starting_stress + opening_path.stress_delta
    starting_life_satisfaction = preset.starting_life_satisfaction + opening_path.life_satisfaction_delta

    player = PlayerState(
        name=player_name,
        cash=max(0, starting_cash),
        savings=max(0, starting_savings),
        debt=max(0, starting_debt),
        stress=max(0, starting_stress),
        energy=preset.starting_energy,
        life_satisfaction=max(0, starting_life_satisfaction),
        family_support=max(0, family_support),
        academic_strength=preset.academic_strength,
        current_city_id=city_id,
        housing_id=housing_id,
        transport_id=opening_path.starting_transport_id,
        budget_stance_id=opening_path.starting_budget_stance_id,
        opening_path_id=opening_path_id,
        selected_focus_action_id=_starting_focus_action_id(opening_path_id),
        career=CareerState(track_id=opening_path.starting_career_track_id),
        education=EducationState(
            program_id=opening_path.starting_education_program_id,
            is_active=opening_path.starting_education_program_id != "none",
            standing=max(45, min(100, 55 + ((preset.academic_strength - 50) // 2))),
            college_gpa=max(1.8, min(4.0, round(2.2 + ((preset.academic_strength - 50) * 0.03), 2))),
        ),
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
        debt_game_over_threshold=bundle.config.debt_game_over_threshold,
        burnout_stress_threshold=bundle.config.burnout_stress_threshold,
        burnout_energy_threshold=bundle.config.burnout_energy_threshold,
        burnout_streak_limit=bundle.config.burnout_streak_limit,
        housing_miss_limit=bundle.config.housing_miss_limit,
        minimum_parent_fallback_support=bundle.config.minimum_parent_fallback_support,
        player=player,
    )
    clamp_player_state(state)
    append_logs(
        state,
        [
            f"{player_name} just graduated at age {state.start_age}.",
            f"You start in {city.name} as a {preset.name.lower()} taking the {opening_path.name.lower()} path.",
            f"Current setup: {housing_id.replace('_', ' ')}, {opening_path.starting_transport_id.replace('_', ' ')}, {player.career.track_id.replace('_', ' ')}.",
        ],
    )
    return state


def build_rng(seed: int | None, fallback_seed: int) -> Random:
    return Random(seed if seed is not None else fallback_seed)
