from __future__ import annotations

from .models import (
    ActiveTemporaryEffect,
    ExpenseDefinition,
    GameState,
    JobDefinition,
    StatEffects,
    TemporaryEffectDefinition,
)
from .utils import clamp


def _append_message(state: GameState, message: str) -> GameState:
    return state.model_copy(update={"message_log": [*state.message_log, message]})


def _withdraw_liquid_funds(state: GameState, amount: int) -> tuple[GameState, int]:
    remaining = max(0, amount)
    cash_used = min(state.player.cash, remaining)
    remaining -= cash_used
    savings_used = min(state.player.savings, remaining)
    remaining -= savings_used

    player = state.player.model_copy(
        update={
            "cash": state.player.cash - cash_used,
            "savings": state.player.savings - savings_used,
        }
    )
    return state.model_copy(update={"player": player}), remaining


def apply_stat_effects(state: GameState, effects: StatEffects, source_label: str) -> GameState:
    if not effects:
        return state

    updated_values = {
        "cash": state.player.cash,
        "savings": state.player.savings,
        "debt": state.player.debt,
        "stress": state.player.stress,
        "energy": state.player.energy,
    }
    for stat, delta in effects.items():
        if stat in {"cash", "savings", "debt"}:
            updated_values[stat] += delta
        elif stat == "stress":
            updated_values["stress"] = clamp(updated_values["stress"] + delta, 0, state.max_stress)
        elif stat == "energy":
            updated_values["energy"] = clamp(updated_values["energy"] + delta, 0, state.max_energy)

    player = state.player.model_copy(update=updated_values)
    effect_text = ", ".join(f"{key} {value:+d}" for key, value in effects.items())
    return state.model_copy(
        update={"player": player, "message_log": [*state.message_log, f"{source_label}: {effect_text}."]}
    )


def _apply_expense_charge(
    state: GameState,
    expense: ExpenseDefinition,
    cost: int,
) -> tuple[GameState, bool]:
    updated_state, uncovered = _withdraw_liquid_funds(state, cost)
    used_debt_for_essential = False

    if uncovered > 0:
        used_debt_for_essential = expense.mandatory
        player = updated_state.player.model_copy(update={"debt": updated_state.player.debt + uncovered})
        updated_state = updated_state.model_copy(update={"player": player})

    payment_source = "cash/savings" if uncovered == 0 else "cash/savings and debt"
    updated_state = _append_message(
        updated_state,
        f"Paid {expense.name} ({cost}) using {payment_source}.",
    )
    return updated_state, used_debt_for_essential


def add_temporary_effects(
    state: GameState,
    temporary_effects: list[TemporaryEffectDefinition],
    source_label: str,
) -> GameState:
    if not temporary_effects:
        return state

    active_effects = [*state.temporary_effects]
    messages = [*state.message_log]
    for effect in temporary_effects:
        active_effects.append(
            ActiveTemporaryEffect(
                id=effect.id,
                label=effect.label,
                remaining_weeks=effect.duration_weeks,
                effects=effect.effects,
            )
        )
        messages.append(
            f"{source_label} created temporary effect '{effect.label}' ({effect.duration_weeks} week(s))."
        )
    return state.model_copy(update={"temporary_effects": active_effects, "message_log": messages})


def apply_start_of_week_temporary_effects(state: GameState) -> GameState:
    updated_state = state
    for effect in state.temporary_effects:
        updated_state = apply_stat_effects(
            updated_state,
            effect.effects,
            f"Temporary effect active ({effect.label})",
        )
    return updated_state


def decrement_temporary_effects(state: GameState, active_effects_at_week_start: int | None = None) -> GameState:
    if not state.temporary_effects:
        return state

    decrement_count = len(state.temporary_effects) if active_effects_at_week_start is None else active_effects_at_week_start
    kept_effects: list[ActiveTemporaryEffect] = []
    messages = [*state.message_log]

    for index, effect in enumerate(state.temporary_effects):
        if index >= decrement_count:
            kept_effects.append(effect)
            continue

        remaining = effect.remaining_weeks - 1
        if remaining <= 0:
            messages.append(f"Temporary effect expired: {effect.label}.")
        else:
            kept_effects.append(effect.model_copy(update={"remaining_weeks": remaining}))

    return state.model_copy(update={"temporary_effects": kept_effects, "message_log": messages})


def apply_mandatory_weekly_expenses(
    state: GameState,
    expenses: list[ExpenseDefinition],
    expense_multiplier: float = 1.0,
) -> GameState:
    updated_state = state
    used_debt_for_essentials = False

    for expense in expenses:
        if expense.cadence != "weekly" or not expense.mandatory:
            continue
        cost = int(round(expense.amount * expense_multiplier))
        updated_state, used_debt = _apply_expense_charge(updated_state, expense, cost)
        used_debt_for_essentials = used_debt_for_essentials or used_debt

    missed_essentials = updated_state.missed_essential_weeks + (1 if used_debt_for_essentials else 0)
    return updated_state.model_copy(update={"missed_essential_weeks": missed_essentials})


def apply_optional_weekly_expenses(
    state: GameState,
    expenses: list[ExpenseDefinition],
    decisions: dict[str, bool] | None = None,
    expense_multiplier: float = 1.0,
) -> GameState:
    updated_state = state
    resolved_decisions = decisions or {}

    for expense in expenses:
        if expense.cadence != "weekly" or expense.mandatory:
            continue

        should_pay = resolved_decisions.get(expense.id, True)
        if should_pay:
            cost = int(round(expense.amount * expense_multiplier))
            updated_state, _ = _apply_expense_charge(updated_state, expense, cost)
            updated_state = apply_stat_effects(
                updated_state,
                expense.pay_effects,
                f"Optional expense paid ({expense.name})",
            )
            updated_state = add_temporary_effects(
                updated_state,
                expense.pay_temporary_effects,
                f"Optional expense paid ({expense.name})",
            )
        else:
            updated_state = _append_message(updated_state, f"Skipped optional expense: {expense.name}.")
            updated_state = apply_stat_effects(
                updated_state,
                expense.skip_effects,
                f"Optional expense skipped ({expense.name})",
            )
            updated_state = add_temporary_effects(
                updated_state,
                expense.skip_temporary_effects,
                f"Optional expense skipped ({expense.name})",
            )

    return updated_state


def apply_weekly_expenses(
    state: GameState,
    expenses: list[ExpenseDefinition],
    expense_multiplier: float = 1.0,
) -> GameState:
    updated_state = apply_mandatory_weekly_expenses(state, expenses, expense_multiplier=expense_multiplier)
    default_pay_all_optional = {
        expense.id: True
        for expense in expenses
        if expense.cadence == "weekly" and not expense.mandatory
    }
    return apply_optional_weekly_expenses(
        updated_state,
        expenses,
        decisions=default_pay_all_optional,
        expense_multiplier=expense_multiplier,
    )


def apply_weekly_income(
    state: GameState,
    job: JobDefinition | None,
    income_multiplier: float = 1.0,
    stress_multiplier: float = 1.0,
) -> GameState:
    if job is None:
        return _append_message(state, "No job income this week.")

    gross_income = int(round(job.hourly_pay * job.hours_per_week * income_multiplier))
    stress_delta = int(round(job.stress_delta * stress_multiplier))
    energy_loss = job.energy_cost

    player = state.player.model_copy(
        update={
            "cash": state.player.cash + gross_income,
            "stress": max(0, state.player.stress + stress_delta),
            "energy": max(0, state.player.energy - energy_loss),
        }
    )
    updated_state = state.model_copy(update={"player": player})
    return _append_message(updated_state, f"Worked as {job.name} and earned {gross_income}.")


def apply_rest_action(state: GameState) -> GameState:
    player = state.player.model_copy(
        update={
            "energy": clamp(state.player.energy + 18, 0, state.max_energy),
            "stress": clamp(state.player.stress - 10, 0, state.max_stress),
        }
    )
    return state.model_copy(update={"player": player, "message_log": [*state.message_log, "Took a rest-focused week."]})


def apply_interest_and_fees(
    state: GameState,
    interest_rate: float,
    overdraft_fee: int,
) -> GameState:
    updated_state = state
    if updated_state.player.debt > 0:
        interest = max(1, int(round(updated_state.player.debt * interest_rate)))
        player = updated_state.player.model_copy(update={"debt": updated_state.player.debt + interest})
        updated_state = updated_state.model_copy(update={"player": player})
        updated_state = _append_message(updated_state, f"Debt interest added {interest}.")

    if updated_state.player.cash < 0:
        player = updated_state.player.model_copy(update={"debt": updated_state.player.debt + overdraft_fee, "cash": 0})
        updated_state = updated_state.model_copy(update={"player": player})
        updated_state = _append_message(updated_state, f"Overdraft fee added {overdraft_fee} to debt.")

    player = updated_state.player.model_copy(
        update={
            "stress": clamp(updated_state.player.stress, 0, updated_state.max_stress),
            "energy": clamp(updated_state.player.energy, 0, updated_state.max_energy),
        }
    )
    return updated_state.model_copy(update={"player": player})
