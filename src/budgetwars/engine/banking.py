from __future__ import annotations

from budgetwars.models import ContentBundle, GameState, ServiceDefinition

from .effects import append_log


def local_services(state: GameState, bundle: ContentBundle, kind: str | None = None) -> list[ServiceDefinition]:
    services = [service for service in bundle.services if state.player.current_district_id in service.district_ids]
    if kind is not None:
        services = [service for service in services if service.kind == kind]
    return services


def deposit_cash(state: GameState, bundle: ContentBundle, amount: int) -> GameState:
    if amount <= 0:
        raise ValueError("Deposit amount must be positive")
    if not local_services(state, bundle, "bank"):
        raise ValueError("There is no bank here")
    if state.player.cash < amount:
        raise ValueError("Not enough cash")
    updated_player = state.player.model_copy(
        update={"cash": state.player.cash - amount, "bank_balance": state.player.bank_balance + amount}
    )
    state = state.model_copy(update={"player": updated_player})
    return append_log(state, f"Deposited ${amount}.")


def withdraw_cash(state: GameState, bundle: ContentBundle, amount: int) -> GameState:
    if amount <= 0:
        raise ValueError("Withdraw amount must be positive")
    if not local_services(state, bundle, "bank"):
        raise ValueError("There is no bank here")
    if state.player.bank_balance < amount:
        raise ValueError("Not enough bank balance")
    updated_player = state.player.model_copy(
        update={"cash": state.player.cash + amount, "bank_balance": state.player.bank_balance - amount}
    )
    state = state.model_copy(update={"player": updated_player})
    return append_log(state, f"Withdrew ${amount}.")


def borrow_cash(state: GameState, bundle: ContentBundle, amount: int) -> GameState:
    if amount <= 0:
        raise ValueError("Borrow amount must be positive")
    lenders = [service for service in local_services(state, bundle, "bank") if service.loan_available]
    if not lenders:
        raise ValueError("No lender is available here")
    if state.player.debt + amount > bundle.config.loan_limit:
        raise ValueError("That would push you past the loan limit")
    updated_player = state.player.model_copy(update={"cash": state.player.cash + amount, "debt": state.player.debt + amount})
    state = state.model_copy(update={"player": updated_player})
    return append_log(state, f"Borrowed ${amount}.")


def repay_debt(state: GameState, bundle: ContentBundle, amount: int) -> GameState:
    if amount <= 0:
        raise ValueError("Repayment amount must be positive")
    if not local_services(state, bundle, "bank"):
        raise ValueError("There is no bank here")
    if state.player.cash < amount:
        raise ValueError("Not enough cash")
    if state.player.debt <= 0:
        raise ValueError("You are not carrying debt")
    actual_amount = min(amount, state.player.debt)
    updated_player = state.player.model_copy(update={"cash": state.player.cash - actual_amount, "debt": state.player.debt - actual_amount})
    state = state.model_copy(update={"player": updated_player})
    return append_log(state, f"Repaid ${actual_amount} of debt.")
