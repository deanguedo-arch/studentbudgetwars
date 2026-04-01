from __future__ import annotations

from collections.abc import Iterable

from budgetwars.models import ActiveMonthlyModifier, ContentBundle, GameState, ModifierTemplate


NUMERIC_PLAYER_KEYS = {
    "cash",
    "savings",
    "debt",
    "stress",
    "energy",
    "life_satisfaction",
    "family_support",
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
    player.cash = int(round(player.cash))
    player.savings = int(round(player.savings))
    player.debt = max(0, int(round(player.debt)))
    player.monthly_surplus = int(round(player.monthly_surplus))
    player.career.promotion_progress = max(0, int(round(player.career.promotion_progress)))
    player.education.months_completed = max(0, int(round(player.education.months_completed)))
    player.education.standing = max(0, min(100, int(round(player.education.standing))))
    player.education.college_gpa = max(0.0, min(4.0, round(player.education.college_gpa, 2)))


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
        elif key == "stress":
            player.stress += value
        elif key == "energy":
            player.energy += value
        elif key == "life_satisfaction":
            player.life_satisfaction += value
        elif key == "family_support":
            player.family_support += value
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
    return state.player.cash + state.player.savings - state.player.debt
