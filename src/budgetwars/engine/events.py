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
    if event.minimum_stress is not None and player.stress < event.minimum_stress:
        return False
    if event.minimum_debt is not None and player.debt < event.minimum_debt:
        return False
    return True


def eligible_events(bundle: ContentBundle, state: GameState) -> list[EventDefinition]:
    return [event for event in bundle.events if _event_is_eligible(bundle, state, event)]


def event_weight(bundle: ContentBundle, state: GameState, event: EventDefinition) -> float:
    weight = float(event.weight)
    housing = get_housing_option(bundle, state.player.housing_id)
    transport = get_transport_option(bundle, state.player.transport_id)
    if event.id == "roommate_conflict":
        weight *= max(0.05, housing.roommate_event_weight)
    if event.id == "car_repair":
        weight *= max(0.05, transport.repair_event_weight)
    if event.id == "used_car_deal" and transport.access_level >= 3:
        weight *= 0.2
    if event.id == "scholarship_boost":
        if not state.player.education.is_active:
            weight *= 0.2
        elif state.player.education.program_id == "college":
            if state.player.education.college_gpa >= 3.2:
                weight *= 1.4
            elif state.player.education.college_gpa < 2.4:
                weight *= 0.6
    if event.id == "rent_increase" and housing.id == "solo_rental":
        weight *= 1.15
    if event.id == "family_emergency" and get_city(bundle, state.player.current_city_id).id == "hometown":
        weight *= 1.1
    return max(0.05, weight)


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
