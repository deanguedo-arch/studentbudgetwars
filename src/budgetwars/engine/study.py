from __future__ import annotations

from budgetwars.models import ContentBundle, GameState

from .effects import append_log, apply_state_effects
from .lookups import get_district


def rest_for_day(state: GameState, bundle: ContentBundle) -> GameState:
    state = apply_state_effects(
        state,
        bundle,
        {"energy": bundle.config.rest_energy_gain, "stress": -bundle.config.rest_stress_reduction},
        "Rested up",
    )
    district = get_district(bundle, state.player.current_district_id)
    if "quiet" in district.event_tags:
        state = apply_state_effects(state, bundle, {"stress": -2}, "Quiet district")
    return append_log(state, "Took a slower day to recover.")


def study_for_day(state: GameState, bundle: ContentBundle) -> GameState:
    district = get_district(bundle, state.player.current_district_id)
    bonus_points = 1 if {"study", "academic", "quiet"} & set(district.event_tags) else 0
    state = apply_state_effects(
        state,
        bundle,
        {
            "energy": -bundle.config.study_energy_cost,
            "stress": bundle.config.study_stress_delta,
            "study_points": bundle.config.study_points_per_action + bonus_points,
        },
        "Studied",
    )
    if bonus_points:
        state = append_log(state, f"{district.name} helped you lock in extra study progress.")
    return state
