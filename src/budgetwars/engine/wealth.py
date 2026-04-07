from __future__ import annotations

from random import Random

from budgetwars.models import ContentBundle, GameState

from .effects import append_log
from .lookups import get_wealth_strategy


def apply_wealth_allocations(bundle: ContentBundle, state: GameState) -> dict[str, int]:
    strategy = get_wealth_strategy(bundle, state.player.wealth_strategy_id)
    # Respect global emergency fund floor
    floor = max(strategy.emergency_cash_floor, bundle.config.emergency_fund_floor)
    available = max(0, state.player.cash - floor)
    if available <= 0:
        return {"safe": 0, "index": 0, "growth": 0, "extra_debt": 0}

    safe_amount = min(state.player.cash, int(round(available * strategy.safe_savings_rate)))
    state.player.cash -= safe_amount
    state.player.high_interest_savings += safe_amount

    index_amount = min(state.player.cash, int(round(available * strategy.index_invest_rate)))
    state.player.cash -= index_amount
    state.player.index_fund += index_amount

    growth_amount = min(state.player.cash, int(round(available * strategy.growth_invest_rate)))
    state.player.cash -= growth_amount
    state.player.aggressive_growth_fund += growth_amount

    extra_debt = min(state.player.cash, int(round(available * strategy.extra_debt_payment_rate)))
    state.player.cash -= extra_debt
    if extra_debt:
        state.player.debt = max(0, state.player.debt - extra_debt)

    if strategy.risk_bias >= 75 and state.player.debt >= 12000:
        state.player.stress += 1
        append_log(state, "You leaned into risk while still carrying real debt pressure.")
    if strategy.liquidity_bias >= 75 and state.player.cash < strategy.emergency_cash_floor:
        state.player.life_satisfaction -= 1
        append_log(state, "You kept the plan defensive because the cash buffer still feels too thin.")

    if safe_amount or index_amount or growth_amount or extra_debt:
        append_log(
            state,
            f"Wealth strategy {strategy.name}: "
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
        total_gain = safe_gain + index_gain + growth_gain
        if total_gain > 50:
            append_log(
                state,
                f"Market regime: {regime.name}. Your invested money is working for you (+${total_gain} total).",
            )
        else:
            append_log(
                state,
                f"Market regime: {regime.name}. Returns -> safe {safe_gain:+d}, index {index_gain:+d}, growth {growth_gain:+d}.",
            )
    else:
        append_log(state, f"Market regime: {regime.name}.")
    
    _check_wealth_milestones(bundle, state)
    _check_rebalance_trigger(bundle, state, regime.id)
    
    return safe_gain, index_gain, growth_gain, regime.name


def emergency_liquidation(state: GameState, shortfall: int) -> int:
    raised = 0
    
    take_growth = min(shortfall, state.player.aggressive_growth_fund)
    state.player.aggressive_growth_fund -= take_growth
    raised += take_growth
    shortfall -= take_growth
    
    take_index = min(shortfall, state.player.index_fund)
    state.player.index_fund -= take_index
    raised += take_index
    shortfall -= take_index
    
    take_safe = min(shortfall, state.player.high_interest_savings)
    state.player.high_interest_savings -= take_safe
    raised += take_safe
    shortfall -= take_safe
    
    if raised > 0:
        state.player.emergency_liquidation_count += 1
        append_log(state, f"EMERGENCY LIQUIDATION: Sold ${raised} of investments to cover severe cash shortfall.")
        state.player.stress += 5
        state.player.life_satisfaction -= 3
        
    return raised


def _check_wealth_milestones(bundle: ContentBundle, state: GameState) -> None:
    invested = state.player.high_interest_savings + state.player.index_fund + state.player.aggressive_growth_fund
    for threshold in sorted(bundle.config.wealth_milestone_thresholds):
        s_thresh = str(threshold)
        if invested >= threshold and s_thresh not in state.player.wealth_milestones_hit:
            state.player.wealth_milestones_hit.append(s_thresh)
            state.player.life_satisfaction += 1
            if threshold >= 5000:
                state.player.stress = max(0, state.player.stress - 2)
            append_log(state, f"Portfolio Milestone: You crossed ${threshold} in total investments!")


def _check_rebalance_trigger(bundle: ContentBundle, state: GameState, regime_id: str) -> None:
    strategy = get_wealth_strategy(bundle, state.player.wealth_strategy_id)
    trigger = strategy.rebalance_trigger
    
    if regime_id == "correction":
        state.player.consecutive_correction_months += 1
    else:
        state.player.consecutive_correction_months = 0
        
    if not trigger:
        return

    if trigger == "protect_floor":
        total_liquid = state.player.cash + state.player.savings
        floor = max(strategy.emergency_cash_floor, bundle.config.emergency_fund_floor)
        if total_liquid < floor:
            shortfall = floor - total_liquid
            raised = emergency_liquidation(state, shortfall)
            if raised > 0:
                state.player.cash += raised
                append_log(state, f"{strategy.name} rebalance: Sold ${raised} to restore cash floor.")
                
    elif trigger == "correction_shift":
        if state.player.consecutive_correction_months >= 2:
            safe_shift = int(state.player.index_fund * 0.2)
            if safe_shift > 0:
                state.player.index_fund -= safe_shift
                state.player.high_interest_savings += safe_shift
                append_log(state, f"{strategy.name} rebalance: Moved ${safe_shift} from index to safe savings to weather the correction.")
                
    elif trigger == "shift_on_debt_clear":
        if state.player.debt <= 2000:
            state.player.wealth_strategy_id = "steady_builder"
            append_log(state, f"Debt crushed! Auto-shifted wealth strategy to Steady Builder.")
