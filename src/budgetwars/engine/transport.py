from __future__ import annotations

from budgetwars.models import ContentBundle, GameState, TransportOptionDefinition

from .effects import append_log
from .lookups import get_city, get_transport_option


def monthly_transport_cost(bundle: ContentBundle, state: GameState, *, modifier_delta: int = 0) -> int:
    transport = get_transport_option(bundle, state.player.transport_id)
    city = get_city(bundle, state.player.current_city_id)
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)
    cost = (
        transport.monthly_payment
        + transport.insurance_cost
        + transport.fuel_maintenance_cost
    ) * city.transport_cost_multiplier * difficulty.transport_cost_multiplier
    return max(0, int(round(cost + modifier_delta)))


def can_switch_transport(bundle: ContentBundle, state: GameState, transport_id: str) -> tuple[bool, str]:
    transport = get_transport_option(bundle, transport_id)
    if transport.id == state.player.transport_id:
        return False, "You already use that transport setup."
    return True, ""


def apply_transport_effects(bundle: ContentBundle, state: GameState) -> TransportOptionDefinition:
    transport = get_transport_option(bundle, state.player.transport_id)
    city = get_city(bundle, state.player.current_city_id)
    state.player.stress += transport.commute_stress_delta
    state.player.energy -= max(0, transport.commute_time_modifier)
    if transport.reliability < 0.7:
        state.player.life_satisfaction -= 1
    state.player.transport.months_owned += 1
    base_reliability = int(round(transport.reliability * 100))
    drift = 0
    if transport.id == "beater_car":
        drift -= 2
    if transport.id == "financed_car":
        drift -= 1
    if state.player.transport.recent_switch_penalty_months > 0:
        state.player.transport.recent_switch_penalty_months -= 1
        drift -= 1
        state.player.stress += 1
    if city.id == "hometown_low_cost" and transport.access_level <= 1:
        state.player.stress += 2
        state.player.energy -= 1
    if city.id == "high_opportunity_metro" and transport.id == "none":
        state.player.stress += 1
    state.player.transport.reliability_score = max(
        0,
        min(100, state.player.transport.reliability_score + drift + (1 if state.player.transport.months_owned > 6 else 0)),
    )
    if state.player.transport.reliability_score > base_reliability + 8:
        state.player.transport.reliability_score = base_reliability + 8
    return transport


def apply_transport_access_penalty(bundle: ContentBundle, state: GameState) -> float:
    transport = get_transport_option(bundle, state.player.transport_id)
    career_track = next(track for track in bundle.careers if track.id == state.player.career.track_id)
    if transport.access_level >= career_track.minimum_transport_access:
        if state.player.transport.reliability_score < 45:
            state.player.stress += 2
            state.player.energy -= 2
            append_log(state, "Transport unreliability chipped away at your workable hours.")
            return 0.92
        return 1.0
    state.player.stress += 4
    state.player.energy -= 5
    append_log(state, "Your transport setup limited the work you could actually take this month.")
    return 0.74
