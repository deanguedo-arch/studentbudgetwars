from __future__ import annotations

from budgetwars.models import ContentBundle, GameState

from .effects import append_log, apply_state_effects
from .lookups import get_district


def move_to_district(state: GameState, bundle: ContentBundle, district_id: str) -> GameState:
    if district_id == state.player.current_district_id:
        raise ValueError("You are already in that district")
    district = get_district(bundle, district_id)
    if state.player.cash < district.travel_cost:
        raise ValueError("Not enough cash to travel there")
    updated_player = state.player.model_copy(
        update={"cash": state.player.cash - district.travel_cost, "current_district_id": district.id}
    )
    state = state.model_copy(update={"player": updated_player})
    state = apply_state_effects(
        state,
        bundle,
        {"energy": -district.travel_energy_cost, "stress": district.travel_stress_delta},
        district.name,
    )
    return append_log(state, f"Traveled to {district.name} for ${district.travel_cost}.")
