from __future__ import annotations

from budgetwars.models import ContentBundle, GameState
from budgetwars.utils import clamp

from .lookups import get_difficulty


def append_log(state: GameState, message: str) -> GameState:
    return state.model_copy(update={"log_messages": [*state.log_messages, message]})


def trim_log(state: GameState, limit: int) -> GameState:
    if limit <= 0:
        return state.model_copy(update={"log_messages": []})
    return state.model_copy(update={"log_messages": state.log_messages[-limit:]})


def apply_state_effects(state: GameState, bundle: ContentBundle, effects: dict[str, float], source: str) -> GameState:
    if not effects:
        return state

    difficulty = get_difficulty(bundle, state.difficulty_id)
    player = state.player
    player_updates = {
        "cash": player.cash,
        "debt": player.debt,
        "bank_balance": player.bank_balance,
        "energy": player.energy,
        "stress": player.stress,
        "heat": player.heat,
        "gpa": player.gpa,
    }
    weekly_study_points = state.weekly_study_points

    for key, raw_delta in effects.items():
        delta = raw_delta
        if key == "cash":
            player_updates["cash"] += int(round(delta))
        elif key == "debt":
            player_updates["debt"] += int(round(delta))
        elif key == "bank_balance":
            player_updates["bank_balance"] += int(round(delta))
        elif key == "energy":
            if delta > 0:
                delta *= difficulty.energy_recovery_multiplier
            player_updates["energy"] = int(round(clamp(player_updates["energy"] + delta, 0, state.max_energy)))
        elif key == "stress":
            if delta > 0:
                delta *= difficulty.stress_multiplier
            player_updates["stress"] = int(round(clamp(player_updates["stress"] + delta, 0, state.max_stress)))
        elif key == "heat":
            player_updates["heat"] = int(round(clamp(player_updates["heat"] + delta, 0, state.max_heat)))
        elif key == "gpa":
            player_updates["gpa"] = float(clamp(player_updates["gpa"] + delta, 0.0, 4.0))
        elif key == "study_points":
            weekly_study_points = max(0, weekly_study_points + int(round(delta)))

    updated_player = player.model_copy(update=player_updates)
    state = state.model_copy(update={"player": updated_player, "weekly_study_points": weekly_study_points})
    effect_text = ", ".join(f"{key} {delta:+g}" for key, delta in effects.items())
    return append_log(state, f"{source}: {effect_text}.")
