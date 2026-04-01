from __future__ import annotations

from collections.abc import Iterable

from budgetwars.models import ActiveMonthlyModifier, AnnualMilestoneSummary, ContentBundle, GameState, ModifierTemplate


NUMERIC_PLAYER_KEYS = {
    "cash",
    "savings",
    "debt",
    "stress",
    "energy",
    "life_satisfaction",
    "family_support",
    "social_stability",
}
PROGRESSION_KEYS = {"promotion_progress", "education_progress"}


def append_log(state: GameState, message: str) -> None:
    if not message.strip():
        return
    state.log_messages.append(message)


def append_logs(state: GameState, messages: Iterable[str]) -> None:
    for message in messages:
        append_log(state, message)


def trim_logs(bundle: ContentBundle, state: GameState) -> None:
    limit = bundle.config.message_log_limit
    if len(state.log_messages) > limit:
        state.log_messages = state.log_messages[-limit:]


def clamp_player_state(state: GameState) -> None:
    player = state.player
    player.stress = max(0, min(state.max_stress, player.stress))
    player.energy = max(0, min(state.max_energy, player.energy))
    player.life_satisfaction = max(0, min(state.max_life_satisfaction, player.life_satisfaction))
    player.family_support = max(0, min(state.max_family_support, player.family_support))
    player.social_stability = max(0, min(state.max_social_stability, player.social_stability))
    player.cash = int(round(player.cash))
    player.savings = int(round(player.savings))
    player.high_interest_savings = max(0, int(round(player.high_interest_savings)))
    player.index_fund = max(0, int(round(player.index_fund)))
    player.aggressive_growth_fund = max(0, int(round(player.aggressive_growth_fund)))
    player.debt = max(0, int(round(player.debt)))
    player.monthly_income = int(round(player.monthly_income))
    player.monthly_expenses = int(round(player.monthly_expenses))
    player.monthly_surplus = int(round(player.monthly_surplus))
    player.career.promotion_progress = max(0, int(round(player.career.promotion_progress)))
    player.career.layoff_pressure = max(0, int(round(player.career.layoff_pressure)))
    player.education.months_completed = max(0, int(round(player.education.months_completed)))
    player.education.failure_streak = max(0, int(round(player.education.failure_streak)))
    player.education.standing = max(0, min(100, int(round(player.education.standing))))
    player.education.college_gpa = max(0.0, min(4.0, round(player.education.college_gpa, 2)))
    player.housing.months_in_place = max(0, int(round(player.housing.months_in_place)))
    player.housing.missed_payment_streak = max(0, int(round(player.housing.missed_payment_streak)))
    player.housing.move_pressure = max(0, int(round(player.housing.move_pressure)))
    player.housing.housing_stability = max(0, min(100, int(round(player.housing.housing_stability))))
    player.housing.recent_move_penalty_months = max(0, int(round(player.housing.recent_move_penalty_months)))
    player.transport.months_owned = max(0, int(round(player.transport.months_owned)))
    player.transport.breakdown_pressure = max(0, int(round(player.transport.breakdown_pressure)))
    player.transport.reliability_score = max(0, min(100, int(round(player.transport.reliability_score))))
    player.transport.recent_switch_penalty_months = max(0, int(round(player.transport.recent_switch_penalty_months)))
    player.career.promotion_momentum = max(0, min(100, int(round(player.career.promotion_momentum))))
    player.career.transition_penalty_months = max(0, int(round(player.career.transition_penalty_months)))
    player.education.reentry_drag_months = max(0, int(round(player.education.reentry_drag_months)))
    player.education.education_momentum = max(0, min(100, int(round(player.education.education_momentum))))


def _apply_cash_delta(state: GameState, delta: float) -> None:
    player = state.player
    player.cash += int(round(delta))
    if player.cash < 0:
        player.debt += abs(player.cash)
        player.cash = 0


def _apply_savings_delta(state: GameState, delta: float) -> None:
    player = state.player
    player.savings += int(round(delta))
    if player.savings < 0:
        player.debt += abs(player.savings)
        player.savings = 0


def _apply_high_interest_savings_delta(state: GameState, delta: float) -> None:
    player = state.player
    player.high_interest_savings += int(round(delta))
    if player.high_interest_savings < 0:
        player.debt += abs(player.high_interest_savings)
        player.high_interest_savings = 0


def apply_stat_effects(state: GameState, effects: dict[str, float]) -> None:
    player = state.player
    for key, raw_value in effects.items():
        value = int(round(raw_value))
        if key == "cash":
            _apply_cash_delta(state, value)
        elif key == "savings":
            _apply_savings_delta(state, value)
        elif key == "debt":
            player.debt = max(0, player.debt + value)
        elif key == "high_interest_savings":
            _apply_high_interest_savings_delta(state, value)
        elif key == "index_fund":
            player.index_fund = max(0, player.index_fund + value)
        elif key == "aggressive_growth_fund":
            player.aggressive_growth_fund = max(0, player.aggressive_growth_fund + value)
        elif key == "stress":
            player.stress += value
        elif key == "energy":
            player.energy += value
        elif key == "life_satisfaction":
            player.life_satisfaction += value
        elif key == "family_support":
            player.family_support += value
        elif key == "social_stability":
            player.social_stability += value
        elif key == "promotion_progress":
            player.career.promotion_progress = max(0, player.career.promotion_progress + value)
        elif key == "education_progress":
            player.education.months_completed = max(0, player.education.months_completed + value)
    clamp_player_state(state)


def create_modifier(template: ModifierTemplate) -> ActiveMonthlyModifier:
    return ActiveMonthlyModifier(
        id=template.id,
        label=template.label,
        remaining_months=template.duration_months,
        stat_effects=dict(template.stat_effects),
        income_multiplier=template.income_multiplier,
        housing_cost_delta=template.housing_cost_delta,
        living_cost_delta=template.living_cost_delta,
        transport_cost_delta=template.transport_cost_delta,
        education_cost_delta=template.education_cost_delta,
        promotion_progress_delta=template.promotion_progress_delta,
        education_progress_delta=template.education_progress_delta,
        transport_switch_discount=template.transport_switch_discount,
    )


def net_worth(state: GameState) -> int:
    return (
        state.player.cash
        + state.player.savings
        + state.player.high_interest_savings
        + state.player.index_fund
        + state.player.aggressive_growth_fund
        - state.player.debt
    )


def summarize_milestone(
    state: GameState,
    *,
    career_tier_label: str,
) -> AnnualMilestoneSummary:
    return AnnualMilestoneSummary(
        year=state.current_year,
        age=state.current_age + 1,
        net_worth=net_worth(state),
        monthly_income=state.player.monthly_income,
        monthly_expenses=state.player.monthly_expenses,
        monthly_surplus=state.player.monthly_surplus,
        debt=state.player.debt,
        housing_id=state.player.housing_id,
        career_track_id=state.player.career.track_id,
        career_tier_label=career_tier_label,
        education_program_id=state.player.education.program_id,
        stress=state.player.stress,
        life_satisfaction=state.player.life_satisfaction,
        summary_lines=[],
    )
