from __future__ import annotations

from dataclasses import dataclass

from budgetwars.models import ContentBundle, GameState

from .effects import append_log
from .lookups import get_budget_stance, get_city


@dataclass
class PaymentResult:
    requested: int
    from_cash: int
    from_savings: int
    added_to_debt: int


def pay_amount(state: GameState, amount: int) -> PaymentResult:
    amount = max(0, int(round(amount)))
    from_cash = min(state.player.cash, amount)
    state.player.cash -= from_cash
    remaining = amount - from_cash
    from_savings = min(state.player.savings, remaining)
    state.player.savings -= from_savings
    remaining -= from_savings
    if remaining > 0:
        state.player.debt += remaining
    return PaymentResult(requested=amount, from_cash=from_cash, from_savings=from_savings, added_to_debt=remaining)


def pay_named_cost(state: GameState, amount: int, label: str) -> PaymentResult:
    result = pay_amount(state, amount)
    message = f"{label}: ${result.requested}"
    if result.added_to_debt:
        message += f" (${result.added_to_debt} rolled into debt)"
    append_log(state, message)
    return result


def make_debt_payment(state: GameState, amount: int) -> int:
    amount = max(0, int(round(amount)))
    paid_from_cash = min(state.player.cash, amount)
    state.player.cash -= paid_from_cash
    remaining = amount - paid_from_cash
    paid_from_savings = min(state.player.savings, remaining)
    state.player.savings -= paid_from_savings
    total_paid = paid_from_cash + paid_from_savings
    if total_paid:
        state.player.debt = max(0, state.player.debt - total_paid)
    append_log(state, f"Debt payment: ${total_paid}" + (f" (short by ${amount - total_paid})" if total_paid < amount else ""))
    return total_paid


def living_cost(bundle: ContentBundle, state: GameState, *, modifier_delta: int = 0) -> int:
    city = get_city(bundle, state.player.current_city_id)
    total = (
        bundle.config.living_cost_food
        + bundle.config.living_cost_phone
        + bundle.config.living_cost_utilities
        + bundle.config.living_cost_insurance
        + bundle.config.living_cost_misc_essentials
    )
    return max(0, int(round((total * city.living_cost_multiplier) + modifier_delta)))


def debt_payment_due(bundle: ContentBundle, state: GameState) -> int:
    if state.player.debt <= 0:
        return 0
    stance = get_budget_stance(bundle, state.player.budget_stance_id)
    baseline = max(bundle.config.minimum_debt_payment, int(round(state.player.debt * bundle.config.debt_payment_rate)))
    return max(0, int(round(baseline * stance.debt_payment_multiplier)))


def discretionary_spending(bundle: ContentBundle, state: GameState) -> int:
    stance = get_budget_stance(bundle, state.player.budget_stance_id)
    return stance.discretionary_spending


def apply_budget_stance(bundle: ContentBundle, state: GameState, available_cash_before_savings: int) -> int:
    stance = get_budget_stance(bundle, state.player.budget_stance_id)
    state.player.stress += stance.stress_delta
    state.player.energy += stance.energy_delta
    state.player.life_satisfaction += stance.life_satisfaction_delta
    state.player.social_stability += stance.social_stability_delta
    contribution = max(0, int(round(max(0, available_cash_before_savings) * stance.savings_contribution_rate)))
    contribution = min(contribution, state.player.cash)
    if contribution:
        state.player.cash -= contribution
        state.player.savings += contribution
        append_log(state, f"Savings transfer: ${contribution}")
    return contribution


def apply_interest_and_growth(bundle: ContentBundle, state: GameState) -> tuple[int, int]:
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)
    interest = int(round(state.player.debt * bundle.config.debt_interest_rate * difficulty.interest_multiplier))
    if interest:
        state.player.debt += interest
        append_log(state, f"Debt interest: +${interest}")
    savings_growth = int(round(state.player.savings * bundle.config.savings_growth_rate))
    if savings_growth:
        state.player.savings += savings_growth
        append_log(state, f"Savings growth: +${savings_growth}")
    return interest, savings_growth
