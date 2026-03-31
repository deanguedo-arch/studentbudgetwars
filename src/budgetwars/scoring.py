from __future__ import annotations

from .models import FinalScoreSummary, GameState, ScoringDefinition


def calculate_final_score(state: GameState, scoring: ScoringDefinition) -> FinalScoreSummary:
    breakdown = {
        "cash": state.player.cash * scoring.cash_weight,
        "savings": state.player.savings * scoring.savings_weight,
        "debt": state.player.debt * scoring.debt_weight,
        "stress": state.player.stress * scoring.stress_weight,
        "energy": state.player.energy * scoring.energy_weight,
    }
    survived_term = state.current_week > state.term_weeks and state.game_over_reason is None
    bonus = scoring.survival_bonus if survived_term else 0.0
    breakdown["survival_bonus"] = bonus

    raw_score = sum(breakdown.values())
    final_score = max(raw_score, scoring.failure_floor)
    outcome = "survived" if survived_term else "failed"

    return FinalScoreSummary(
        final_score=final_score,
        survived_term=survived_term,
        outcome=outcome,
        breakdown=breakdown,
    )


def calculate_score(state: GameState, scoring: ScoringDefinition) -> float:
    return calculate_final_score(state, scoring).final_score
