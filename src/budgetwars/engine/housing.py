from __future__ import annotations

from budgetwars.models import ContentBundle, GameState, HousingOptionDefinition

from .effects import append_log
from .lookups import get_city, get_housing_option


def monthly_housing_cost(bundle: ContentBundle, state: GameState, *, modifier_delta: int = 0) -> int:
    housing = get_housing_option(bundle, state.player.housing_id)
    city = get_city(bundle, state.player.current_city_id)
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)
    cost = housing.base_monthly_cost * city.housing_cost_multiplier * difficulty.housing_cost_multiplier
    return max(0, int(round(cost + modifier_delta)))


def can_switch_housing(bundle: ContentBundle, state: GameState, housing_id: str) -> tuple[bool, str]:
    housing = get_housing_option(bundle, housing_id)
    if housing.id == state.player.housing_id:
        return False, "You already live there."
    if housing.requires_hometown and state.player.current_city_id != "hometown_low_cost":
        return False, "You can only stay with parents in the hometown low-cost city."
    if housing.minimum_family_support and state.player.family_support < housing.minimum_family_support:
        return False, "Your family support is too low for that fallback right now."
    if housing.student_only and (not state.player.education.is_active or state.player.education.program_id == "none"):
        return False, "Student residence only makes sense while you are actively enrolled."
    return True, ""


def apply_housing_effects(bundle: ContentBundle, state: GameState) -> HousingOptionDefinition:
    housing = get_housing_option(bundle, state.player.housing_id)
    state.player.stress += housing.stress_delta
    state.player.life_satisfaction += housing.life_satisfaction_delta
    state.player.social_stability += housing.social_stability_delta
    state.player.housing.months_in_place += 1
    if (
        housing.id == "parents"
        and state.player.current_city_id == "hometown_low_cost"
        and state.player.career.track_id in {"retail_service", "delivery_gig"}
        and state.player.education.program_id == "none"
    ):
        state.player.family_support -= bundle.config.parent_drift_family_penalty
        state.player.life_satisfaction -= bundle.config.parent_drift_satisfaction_penalty
        state.player.social_stability -= bundle.config.parent_drift_social_penalty
        append_log(state, "Living at home saved money, but the sense of drifting hit harder this month.")
    return housing
