from __future__ import annotations

from budgetwars.models import ContentBundle, GameState, HousingOptionDefinition

import random

from .effects import append_log
from .lookups import get_city, get_housing_option


def monthly_housing_cost(bundle: ContentBundle, state: GameState, *, modifier_delta: int = 0) -> int:
    housing = get_housing_option(bundle, state.player.housing_id)
    city = get_city(bundle, state.player.current_city_id)
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)
    cost = housing.base_monthly_cost * city.housing_cost_multiplier * difficulty.housing_cost_multiplier * state.player.housing.base_rent_multiplier
    return max(0, int(round(cost + modifier_delta)))


def can_switch_housing(bundle: ContentBundle, state: GameState, housing_id: str) -> tuple[bool, str]:
    housing = get_housing_option(bundle, housing_id)
    player = state.player
    if housing.id == state.player.housing_id:
        return False, "You already live there."
    if housing.requires_hometown and player.current_city_id != "hometown_low_cost":
        return False, "You can only stay with parents in the hometown low-cost city."
    if housing.minimum_family_support and player.family_support < housing.minimum_family_support:
        return False, "Your family support is too low for that fallback right now."
    if housing.student_only and (not player.education.is_active or player.education.program_id == "none"):
        return False, "Student residence only makes sense while you are actively enrolled."
    if player.credit_score < housing.minimum_credit_score:
        return False, f"Your credit score ({player.credit_score}) is too low to secure this lease."
    if player.credit_missed_obligation_streak >= 2 and housing.id in {"roommates", "solo_rental"} and player.credit_score < 760:
        return False, "Recent missed obligations are still blocking lease approvals."
    if player.credit_utilization_pressure >= 72 and housing.id == "solo_rental" and player.credit_score < 760:
        return False, "Credit utilization pressure is too high for a solo-lease approval."
    if housing.id == "roommates":
        if player.credit_score < 580 and player.debt >= 9000:
            return False, "Roommate applications are getting denied until credit or debt pressure improves."
        if player.monthly_surplus < -180 and player.credit_score < 620:
            return False, "With this monthly deficit and credit profile, shared-lease approval is unlikely."
        if player.credit_missed_obligation_streak >= 3 and player.credit_score < 700:
            return False, "Recent payment history is too shaky for this shared lease."
    if housing.id == "solo_rental":
        if player.credit_score < 700 and player.debt >= 10000:
            return False, "Solo rental is blocked until credit improves or debt comes down."
        if player.debt >= 14000 and player.credit_score < 740:
            return False, "That lease wants stronger credit or less debt pressure first."
        if player.monthly_surplus < -100 and (player.cash + player.savings) < (housing.move_in_cost + 300):
            return False, "A solo lease on a negative monthly swing is too fragile right now."
    return True, ""


def apply_housing_effects(bundle: ContentBundle, state: GameState) -> HousingOptionDefinition:
    housing = get_housing_option(bundle, state.player.housing_id)
    state.player.stress += housing.stress_delta
    state.player.life_satisfaction += housing.life_satisfaction_delta
    state.player.social_stability += housing.social_stability_delta
    state.player.housing.months_in_place += 1
    
    if state.player.housing.original_quality is None:
        state.player.housing.original_quality = housing.quality_score

    current_quality = housing.quality_score - int(state.player.housing.layout_escalator)

    if housing.id != "parents":
        if state.player.housing.lease_months_remaining > 0:
            state.player.housing.lease_months_remaining -= 1
        elif state.player.housing.months_in_place > 1:
            hike = random.uniform(bundle.config.annual_rent_hike_min, bundle.config.annual_rent_hike_max)
            state.player.housing.base_rent_multiplier *= (1.0 + hike)
            state.player.housing.lease_months_remaining = 11
            state.player.stress += 3
            state.player.life_satisfaction -= 2
            append_log(state, f"Lease renewed. Rent increased by {int(hike*100)}% for the next year.")
            
        if state.player.housing.months_in_place > 0 and state.player.housing.months_in_place % 6 == 0:
            state.player.housing.layout_escalator += 1
            if int(state.player.housing.layout_escalator) % 3 == 0:
                append_log(state, "The apartment is showing its age. Living with the unfixed issues is draining.")
                state.player.life_satisfaction -= 1

    state.player.housing.housing_stability = min(
        100,
        max(
            0,
            state.player.housing.housing_stability
            + int(round((current_quality - 55) / 12))
            + (1 if state.player.housing.months_in_place >= 4 else 0),
        ),
    )
    if state.player.housing.recent_move_penalty_months > 0:
        state.player.housing.recent_move_penalty_months -= 1
        state.player.housing.housing_stability = max(0, state.player.housing.housing_stability - 3)
        state.player.stress += 2
        state.player.social_stability -= 1
    if (
        housing.id == "parents"
        and state.player.current_city_id == "hometown_low_cost"
        and state.player.career.track_id in {"retail_service", "delivery_gig"}
        and state.player.education.program_id == "none"
    ):
        state.player.family_support -= bundle.config.parent_drift_family_penalty
        state.player.life_satisfaction -= bundle.config.parent_drift_satisfaction_penalty
        state.player.social_stability -= bundle.config.parent_drift_social_penalty
        state.player.housing.housing_stability = max(0, state.player.housing.housing_stability - 2)
        append_log(state, "Living at home saved money, but the sense of drifting hit harder this month.")
    if housing.id == "roommates":
        if state.player.social_stability < 45:
            state.player.housing.housing_stability = max(0, state.player.housing.housing_stability - 2)
            state.player.stress += 1
        elif state.player.social_stability >= 65:
            state.player.housing.housing_stability = min(100, state.player.housing.housing_stability + 1)
    if housing.id == "solo_rental" and state.player.monthly_surplus < 0:
        state.player.housing.housing_stability = max(0, state.player.housing.housing_stability - 3)
        state.player.stress += 2
    return housing
