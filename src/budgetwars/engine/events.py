from __future__ import annotations

from random import Random

from budgetwars.models import ContentBundle, EventDefinition, GameState

from .effects import append_log, apply_stat_effects, create_modifier
from .lookups import get_city, get_housing_option, get_transport_option


def _event_is_eligible(bundle: ContentBundle, state: GameState, event: EventDefinition) -> bool:
    player = state.player
    if state.current_month < event.min_month:
        return False
    if event.eligible_city_ids and player.current_city_id not in event.eligible_city_ids:
        return False
    if event.eligible_housing_ids and player.housing_id not in event.eligible_housing_ids:
        return False
    if event.eligible_transport_ids and player.transport_id not in event.eligible_transport_ids:
        return False
    if event.eligible_career_ids and player.career.track_id not in event.eligible_career_ids:
        return False
    if event.eligible_education_ids and player.education.program_id not in event.eligible_education_ids:
        return False
    if event.eligible_opening_path_ids and player.opening_path_id not in event.eligible_opening_path_ids:
        return False
    if event.minimum_stress is not None and player.stress < event.minimum_stress:
        return False
    if event.minimum_debt is not None and player.debt < event.minimum_debt:
        return False
    if event.minimum_family_support is not None and player.family_support < event.minimum_family_support:
        return False
    if event.maximum_family_support is not None and player.family_support > event.maximum_family_support:
        return False
    if event.minimum_social_stability is not None and player.social_stability < event.minimum_social_stability:
        return False
    if event.maximum_social_stability is not None and player.social_stability > event.maximum_social_stability:
        return False
    if event.maximum_transport_reliability is not None and player.transport.reliability_score > event.maximum_transport_reliability:
        return False
    if event.maximum_housing_stability is not None and player.housing.housing_stability > event.maximum_housing_stability:
        return False
    if event.maximum_life_satisfaction is not None and player.life_satisfaction > event.maximum_life_satisfaction:
        return False
    if event.eligible_market_regime_ids and state.current_market_regime_id not in event.eligible_market_regime_ids:
        return False
    return True


def eligible_events(bundle: ContentBundle, state: GameState) -> list[EventDefinition]:
    return [event for event in bundle.events if _event_is_eligible(bundle, state, event)]


def event_weight(bundle: ContentBundle, state: GameState, event: EventDefinition) -> float:
    weight = float(event.weight)
    housing = get_housing_option(bundle, state.player.housing_id)
    transport = get_transport_option(bundle, state.player.transport_id)
    city = get_city(bundle, state.player.current_city_id)
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)

    if event.id == "roommate_conflict":
        weight *= max(0.05, housing.roommate_event_weight)
    if event.id == "car_repair":
        weight *= max(0.05, transport.repair_event_weight)
    if event.id == "used_car_window" and transport.access_level >= 3:
        weight *= 0.2
    if event.id == "promotion_window":
        track = next(track for track in bundle.careers if track.id == state.player.career.track_id)
        weight *= track.promotion_weight
    if event.id == "job_layoff":
        track = next(track for track in bundle.careers if track.id == state.player.career.track_id)
        weight *= track.layoff_weight
    if event.id == "scholarship_relief":
        if not state.player.education.is_active:
            weight *= 0.2
        elif state.player.education.college_gpa >= 3.2:
            weight *= 1.5
        elif state.player.education.college_gpa < 2.3:
            weight *= 0.65
    if event.id == "rent_increase" and housing.id == "solo_rental":
        weight *= 1.2
    if event.id == "family_emergency" and city.id == "hometown_low_cost":
        weight *= 1.15
    if event.id == "family_emergency" and state.player.family_support <= 35:
        weight *= 1.25
    if event.id == "burnout_month" and state.player.selected_focus_action_id in {"overtime", "promotion_hunt"}:
        weight *= 1.15
    if event.id == "burnout_month" and state.player.career.transition_penalty_months > 0:
        weight *= 1.2
    if event.id == "side_hustle_window" and state.player.selected_focus_action_id == "side_gig":
        weight *= 1.35
    if event.id == "job_layoff" and state.player.career.recent_performance_tag == "downtrend":
        weight *= 1.2
    if event.id == "job_layoff" and state.player.career.recent_performance_tag == "uptrend":
        weight *= 0.85
    if event.id == "rent_increase" and state.player.housing.housing_stability < 45:
        weight *= 1.15
    if event.id == "car_repair" and state.player.transport.reliability_score < 55:
        weight *= 1.35
    if event.id == "car_repair" and state.player.transport.option_id == "financed_car":
        weight *= 1.1
    if event.id == "used_car_window" and state.current_market_regime_id in {"weak", "correction"}:
        weight *= 1.2
    if event.id == "economic_downturn" and state.current_market_regime_id in {"weak", "correction"}:
        weight *= 1.25
    if event.id == "scholarship_relief" and state.player.education.education_momentum >= 60:
        weight *= 1.2

    return max(0.05, weight * difficulty.event_weight_multiplier)


def pick_event(bundle: ContentBundle, state: GameState, rng: Random, excluded_ids: set[str] | None = None) -> EventDefinition | None:
    candidates = [event for event in eligible_events(bundle, state) if not excluded_ids or event.id not in excluded_ids]
    if not candidates:
        return None
    weights = [event_weight(bundle, state, event) for event in candidates]
    return rng.choices(candidates, weights=weights, k=1)[0]


def resolve_event(bundle: ContentBundle, state: GameState, event: EventDefinition) -> None:
    apply_stat_effects(state, event.immediate_effects)
    if event.modifier is not None:
        state.active_modifiers.append(create_modifier(event.modifier))
        append_log(state, f"Modifier gained: {event.modifier.label} ({event.modifier.duration_months} months)")
    append_log(state, event.log_entry or event.name)


def roll_month_events(bundle: ContentBundle, state: GameState, rng: Random) -> list[EventDefinition]:
    rolled: list[EventDefinition] = []
    excluded: set[str] = set()
    if rng.random() < bundle.config.primary_event_chance:
        event = pick_event(bundle, state, rng, excluded)
        if event:
            resolve_event(bundle, state, event)
            rolled.append(event)
            excluded.add(event.id)
    if rng.random() < bundle.config.secondary_event_chance:
        event = pick_event(bundle, state, rng, excluded)
        if event:
            resolve_event(bundle, state, event)
            rolled.append(event)
    return rolled
