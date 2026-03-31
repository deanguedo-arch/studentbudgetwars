from __future__ import annotations

from budgetwars.models import ContentBundle, FinalScoreSummary, GameState

from .inventory import estimated_inventory_value


def calculate_final_score(state: GameState, bundle: ContentBundle) -> FinalScoreSummary:
    inventory_value = estimated_inventory_value(state, bundle)
    net_worth = state.player.cash + state.player.bank_balance + inventory_value - state.player.debt
    survived = (
        state.current_day > state.total_days
        and state.game_over_reason is None
        and state.player.gpa >= state.minimum_survival_gpa
        and net_worth >= state.minimum_survival_net_worth
    )
    breakdown = {
        "cash": float(state.player.cash),
        "bank_balance": float(state.player.bank_balance),
        "inventory_value": float(inventory_value),
        "debt_penalty": float(-state.player.debt),
        "gpa_bonus": float(state.player.gpa * 120),
        "energy_bonus": float(state.player.energy * 1.5),
        "stress_penalty": float(-state.player.stress * 1.5),
        "heat_penalty": float(-state.player.heat),
        "survival_bonus": 250.0 if survived else -150.0,
    }
    final_score = round(sum(breakdown.values()), 2)
    outcome = "Survived the term" if survived else (state.game_over_reason or "Did not finish the term cleanly")
    return FinalScoreSummary(final_score=final_score, survived_term=survived, outcome=outcome, breakdown=breakdown)
