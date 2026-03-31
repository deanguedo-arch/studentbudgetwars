from __future__ import annotations

from .models import GameState, LocationDefinition
from .utils import clamp


def location_map(locations: list[LocationDefinition]) -> dict[str, LocationDefinition]:
    return {location.id: location for location in locations}


def get_location(locations: list[LocationDefinition], location_id: str) -> LocationDefinition | None:
    return location_map(locations).get(location_id)


def apply_location_effects(state: GameState, location: LocationDefinition | None) -> GameState:
    if location is None:
        return state.model_copy(update={"message_log": [*state.message_log, "Location effect skipped: unknown location."]})
    if not location.modifiers:
        return state

    updated_values = {
        "cash": state.player.cash,
        "savings": state.player.savings,
        "debt": state.player.debt,
        "stress": state.player.stress,
        "energy": state.player.energy,
    }

    for stat, delta in location.modifiers.items():
        if stat in {"cash", "savings", "debt"}:
            updated_values[stat] += delta
        elif stat == "stress":
            updated_values["stress"] = clamp(updated_values["stress"] + delta, 0, state.max_stress)
        elif stat == "energy":
            updated_values["energy"] = clamp(updated_values["energy"] + delta, 0, state.max_energy)

    player = state.player.model_copy(update=updated_values)
    effect_text = ", ".join(f"{key} {value:+d}" for key, value in location.modifiers.items())
    return state.model_copy(
        update={
            "player": player,
            "message_log": [*state.message_log, f"Location effects ({location.name}): {effect_text}."],
        }
    )


def move_location(
    state: GameState,
    locations: list[LocationDefinition],
    new_location_id: str,
    *,
    stress_penalty: int = 0,
) -> GameState:
    target = get_location(locations, new_location_id)
    if target is None:
        return state.model_copy(update={"message_log": [*state.message_log, f"Invalid location selection: {new_location_id}."]})

    if state.player.location_id == target.id:
        return state.model_copy(update={"message_log": [*state.message_log, f"Already at {target.name}."]})

    updated_stress = clamp(state.player.stress + max(stress_penalty, 0), 0, state.max_stress)
    player = state.player.model_copy(update={"location_id": target.id, "stress": updated_stress})
    move_text = f"Moved to {target.name}."
    if stress_penalty > 0:
        move_text += f" Travel strain +{stress_penalty} stress."
    return state.model_copy(update={"player": player, "message_log": [*state.message_log, move_text]})
