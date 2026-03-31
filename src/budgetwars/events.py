from __future__ import annotations

import random

from .models import EventDefinition, GameState
from .utils import clamp


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

    updated_values = {
        "cash": state.player.cash,
        "savings": state.player.savings,
        "debt": state.player.debt,
        "stress": state.player.stress,
        "energy": state.player.energy,
    }

    for stat, delta in combined_effects.items():
        if stat in {"cash", "savings", "debt"}:
            updated_values[stat] += delta
        elif stat == "stress":
            updated_values["stress"] = clamp(updated_values["stress"] + delta, 0, state.max_stress)
        elif stat == "energy":
            updated_values["energy"] = clamp(updated_values["energy"] + delta, 0, state.max_energy)

    player = state.player.model_copy(update=updated_values)
    choice_text = choice.label if choice is not None else "Default outcome"
    return state.model_copy(
        update={
            "player": player,
            "active_event_ids": [*state.active_event_ids, event.id],
            "message_log": [*state.message_log, f"Event: {event.name} -> {choice_text}."],
        }
    )
