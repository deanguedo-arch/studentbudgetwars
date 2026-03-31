from __future__ import annotations

import random

from budgetwars.models import ActiveWorldEvent, ContentBundle, EventDefinition, GameState
from budgetwars.utils import derive_seed

from .effects import append_log, apply_state_effects
from .lookups import get_district


def _weighted_choice(events: list[EventDefinition], weights: list[float], rng: random.Random) -> EventDefinition:
    total = sum(weights)
    roll = rng.uniform(0, total)
    cursor = 0.0
    for event, weight in zip(events, weights, strict=True):
        cursor += weight
        if roll <= cursor:
            return event
    return events[-1]


def _event_weight(state: GameState, bundle: ContentBundle, event: EventDefinition) -> float:
    district = get_district(bundle, state.player.current_district_id)
    overlap = len(set(event.event_tags) & set(district.event_tags))
    heat_bias = 1.15 if "inspectors" in event.event_tags and state.player.heat > 35 else 1.0
    return event.weight * (1 + (0.35 * overlap)) * heat_bias


def activate_event(state: GameState, bundle: ContentBundle, event: EventDefinition, start_day: int) -> GameState:
    if event.log_entry:
        state = append_log(state, event.log_entry)
    if event.stat_effects:
        state = apply_state_effects(state, bundle, event.stat_effects, event.name)
    if event.duration_days > 0:
        active_event = ActiveWorldEvent(
            event_id=event.id,
            name=event.name,
            description=event.description,
            expires_on_day=start_day + event.duration_days - 1,
            commodity_multipliers=event.commodity_multipliers,
            district_commodity_multipliers=event.district_commodity_multipliers,
            stat_effects=event.stat_effects,
            log_entry=event.log_entry,
        )
        state = state.model_copy(update={"active_events": [*state.active_events, active_event]})
    return state


def prune_expired_events(state: GameState) -> GameState:
    active = [event for event in state.active_events if event.expires_on_day >= state.current_day]
    return state.model_copy(update={"active_events": active})


def roll_weekly_events(state: GameState, bundle: ContentBundle) -> GameState:
    weekly_events = [event for event in bundle.events if event.trigger in {"weekly", "any"}]
    if not weekly_events:
        return state
    rng = random.Random(derive_seed(state.seed, "weekly-events", state.current_week))
    picked_ids: set[str] = set()
    count = min(bundle.config.weekly_market_event_count, len(weekly_events))
    for _ in range(count):
        candidates = [event for event in weekly_events if event.id not in picked_ids]
        if not candidates:
            break
        weights = [_event_weight(state, bundle, event) for event in candidates]
        chosen = _weighted_choice(candidates, weights, rng)
        picked_ids.add(chosen.id)
        state = activate_event(state, bundle, chosen, state.current_day)
    return state


def roll_daily_event(state: GameState, bundle: ContentBundle) -> GameState:
    rng = random.Random(derive_seed(state.seed, "daily-event-roll", state.current_day, state.player.current_district_id))
    if rng.random() > bundle.config.daily_event_chance:
        return state
    daily_events = [event for event in bundle.events if event.trigger in {"daily", "any"}]
    if not daily_events:
        return state
    weights = [_event_weight(state, bundle, event) for event in daily_events]
    chosen = _weighted_choice(daily_events, weights, rng)
    start_day = state.current_day + 1 if chosen.duration_days > 0 else state.current_day
    return activate_event(state, bundle, chosen, start_day)
