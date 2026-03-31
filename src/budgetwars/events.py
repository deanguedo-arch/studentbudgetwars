from __future__ import annotations

import random

from .budget import add_temporary_effects, apply_stat_effects
from .models import EventDefinition, GameState


def roll_event(
    rng: random.Random,
    events: list[EventDefinition],
    event_chance: float = 1.0,
) -> EventDefinition | None:
    if not events or rng.random() > event_chance:
        return None
    weights = [event.weight for event in events]
    return rng.choices(events, weights=weights, k=1)[0]


def resolve_event_choice(
    state: GameState,
    event: EventDefinition,
    choice_id: str | None = None,
) -> GameState:
    choice = None
    if event.choices:
        choice = next((candidate for candidate in event.choices if candidate.id == choice_id), event.choices[0])

    combined_effects = dict(event.effects)
    if choice is not None:
        for key, value in choice.effects.items():
            combined_effects[key] = combined_effects.get(key, 0) + value

    updated_state = apply_stat_effects(state, combined_effects, f"Event effects ({event.name})")
    choice_text = choice.label if choice is not None else "Default outcome"
    updated_state = updated_state.model_copy(
        update={
            "active_event_ids": [*updated_state.active_event_ids, event.id],
            "message_log": [*updated_state.message_log, f"Event: {event.name} -> {choice_text}."],
        }
    )
    event_temporary_effects = [*event.temporary_effects]
    if choice is not None:
        event_temporary_effects.extend(choice.temporary_effects)
    return add_temporary_effects(updated_state, event_temporary_effects, f"Event ({event.name})")
