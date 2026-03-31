from __future__ import annotations

from .models import GameState, ItemDefinition
from .utils import clamp


def buy_item(state: GameState, item: ItemDefinition) -> GameState:
    available_funds = state.player.cash + state.player.savings
    if available_funds < item.price:
        return state.model_copy(
            update={"message_log": [*state.message_log, f"Could not afford {item.name}."]}
        )

    remaining_price = item.price
    cash_used = min(state.player.cash, remaining_price)
    remaining_price -= cash_used
    savings_used = min(state.player.savings, remaining_price)

    inventory = dict(state.player.inventory)
    inventory[item.id] = inventory.get(item.id, 0) + 1

    updated_values = {
        "cash": state.player.cash - cash_used,
        "savings": state.player.savings - savings_used,
        "stress": state.player.stress,
        "energy": state.player.energy,
        "debt": state.player.debt,
        "inventory": inventory,
    }

    for stat, delta in item.effects.items():
        if stat == "cash":
            updated_values["cash"] += delta
        elif stat == "savings":
            updated_values["savings"] += delta
        elif stat == "debt":
            updated_values["debt"] += delta
        elif stat == "stress":
            updated_values["stress"] = clamp(updated_values["stress"] + delta, 0, state.max_stress)
        elif stat == "energy":
            updated_values["energy"] = clamp(updated_values["energy"] + delta, 0, state.max_energy)

    player = state.player.model_copy(update=updated_values)
    return state.model_copy(
        update={
            "player": player,
            "message_log": [*state.message_log, f"Bought {item.name} for {item.price}."],
        }
    )
