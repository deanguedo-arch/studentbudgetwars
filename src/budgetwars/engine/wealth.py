from __future__ import annotations

from random import Random

from budgetwars.models import ContentBundle, GameState

from .effects import append_log
from .lookups import get_budget_stance


def apply_wealth_allocations(bundle: ContentBundle, state: GameState) -> dict[str, int]:
    stance = get_budget_stance(bundle, state.player.budget_stance_id)
    available = max(0, state.player.cash - stance.emergency_cash_floor)
    if available <= 0:
        return {"safe": 0, "index": 0, "growth": 0, "extra_debt": 0}

    safe_amount = min(state.player.cash, int(round(available * stance.safe_savings_rate)))
    state.player.cash -= safe_amount
    state.player.high_interest_savings += safe_amount

    index_amount = min(state.player.cash, int(round(available * stance.index_invest_rate)))
    state.player.cash -= index_amount
    state.player.index_fund += index_amount

    growth_amount = min(state.player.cash, int(round(available * stance.growth_invest_rate)))
    state.player.cash -= growth_amount
    state.player.aggressive_growth_fund += growth_amount

    extra_debt = min(state.player.cash, int(round(available * stance.extra_debt_payment_rate)))
    state.player.cash -= extra_debt
    if extra_debt:
        state.player.debt = max(0, state.player.debt - extra_debt)

    if safe_amount or index_amount or growth_amount or extra_debt:
        append_log(
            state,
            "Wealth allocation: "
            f"safe ${safe_amount}, index ${index_amount}, growth ${growth_amount}, debt ${extra_debt}.",
        )
    return {
        "safe": safe_amount,
        "index": index_amount,
        "growth": growth_amount,
        "extra_debt": extra_debt,
    }


def apply_wealth_returns(bundle: ContentBundle, state: GameState, rng: Random) -> tuple[int, int, int, str]:
    regimes = bundle.config.market_regimes
    regime = rng.choices(regimes, weights=[entry.weight for entry in regimes], k=1)[0]
    state.current_market_regime_id = regime.id

    safe_gain = int(round(state.player.high_interest_savings * bundle.config.high_interest_savings_rate))
    index_gain = int(round(state.player.index_fund * regime.index_return_rate))
    growth_gain = int(round(state.player.aggressive_growth_fund * regime.growth_return_rate))

    state.player.high_interest_savings += safe_gain
    state.player.index_fund = max(0, state.player.index_fund + index_gain)
    state.player.aggressive_growth_fund = max(0, state.player.aggressive_growth_fund + growth_gain)

    if safe_gain or index_gain or growth_gain:
        append_log(
            state,
            f"Market regime: {regime.name}. Returns -> safe {safe_gain:+d}, index {index_gain:+d}, growth {growth_gain:+d}.",
        )
    else:
        append_log(state, f"Market regime: {regime.name}.")
    return safe_gain, index_gain, growth_gain, regime.name
