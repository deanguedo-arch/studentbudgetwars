from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import mean

from budgetwars.models import ContentBundle

from .game_loop import GameController


@dataclass
class SimulationRunResult:
    preset_id: str
    difficulty_id: str
    policy_name: str
    seed: int
    survived: bool
    final_score: float
    ending_cash: int
    ending_bank_balance: int
    ending_debt: int
    ending_stress: int
    ending_energy: int
    ending_gpa: float
    ending_district_id: str
    game_over_reason: str | None


def balanced_policy(controller: GameController) -> tuple[str, dict[str, int | str]]:
    state = controller.state
    market = controller.current_market()
    player = state.player

    if player.energy <= 20 or player.stress >= 78:
        return ("rest", {})
    if state.current_week in {2, 4, 6, 9, 12} and state.weekly_study_points < max(2, state.current_week // 2):
        return ("study", {})

    local_bank = any(
        service.kind == "bank" and player.current_district_id in service.district_ids for service in controller.bundle.services
    )
    if player.debt > 0 and player.cash >= min(player.debt, 50) and local_bank:
        return ("repay", {"amount": min(player.debt, 50)})

    for entry in player.commodity_inventory:
        local_price = market.listings[entry.commodity_id]
        if local_price >= int(entry.average_price * 1.22):
            return ("sell", {"commodity_id": entry.commodity_id, "quantity": min(entry.quantity, 3)})

    gigs = controller.available_gigs()
    if gigs and player.energy >= 24:
        gigs = sorted(gigs, key=lambda gig: (gig.pay - (gig.energy_cost * 1.5) - (gig.stress_delta * 3)), reverse=True)
        return ("gig", {"gig_id": gigs[0].id})

    affordable = []
    for commodity in controller.bundle.commodities:
        price = market.listings[commodity.id]
        max_qty = min(player.cash // price, controller.remaining_capacity() // commodity.size)
        if max_qty > 0:
            affordable.append((commodity.id, price, max_qty))
    if affordable:
        commodity_id, price, max_qty = min(affordable, key=lambda item: item[1])
        return ("buy", {"commodity_id": commodity_id, "quantity": max(1, min(max_qty, 2))})

    safer_districts = sorted(controller.bundle.districts, key=lambda district: (district.local_risk, district.travel_cost))
    for district in safer_districts:
        if district.id != player.current_district_id and player.cash >= district.travel_cost:
            return ("travel", {"district_id": district.id})
    return ("rest", {})


def cash_hungry_policy(controller: GameController) -> tuple[str, dict[str, int | str]]:
    state = controller.state
    market = controller.current_market()
    player = state.player

    for entry in player.commodity_inventory:
        local_price = market.listings[entry.commodity_id]
        if local_price >= int(entry.average_price * 1.1):
            return ("sell", {"commodity_id": entry.commodity_id, "quantity": min(entry.quantity, 4)})

    gigs = controller.available_gigs()
    if gigs and player.energy >= 14:
        gigs = sorted(gigs, key=lambda gig: gig.pay - (gig.energy_cost + max(0, gig.stress_delta * 2)), reverse=True)
        return ("gig", {"gig_id": gigs[0].id})

    affordable = []
    for commodity in controller.bundle.commodities:
        price = market.listings[commodity.id]
        max_qty = min(player.cash // price, controller.remaining_capacity() // commodity.size)
        if max_qty > 0:
            affordable.append((commodity.id, price, max_qty))
    if affordable:
        commodity_id, price, max_qty = min(affordable, key=lambda item: item[1])
        quantity = max(1, min(max_qty, 3))
        return ("buy", {"commodity_id": commodity_id, "quantity": quantity})

    if player.energy <= 12:
        return ("rest", {})

    risky_districts = sorted(controller.bundle.districts, key=lambda district: (-district.local_risk, district.travel_cost))
    for district in risky_districts:
        if district.id != player.current_district_id and player.cash >= district.travel_cost:
            return ("travel", {"district_id": district.id})
    return ("study", {})


POLICIES = {"balanced": balanced_policy, "cash_hungry": cash_hungry_policy}


def apply_policy_action(controller: GameController, policy_name: str) -> None:
    if policy_name not in POLICIES:
        raise ValueError(f"Unknown policy '{policy_name}'")
    action, params = POLICIES[policy_name](controller)
    if action == "travel":
        controller.travel(str(params["district_id"]))
    elif action == "buy":
        controller.buy(str(params["commodity_id"]), int(params["quantity"]))
    elif action == "sell":
        controller.sell(str(params["commodity_id"]), int(params["quantity"]))
    elif action == "gig":
        controller.work_gig(str(params["gig_id"]))
    elif action == "study":
        controller.study()
    elif action == "rest":
        controller.rest()
    elif action == "repay":
        controller.bank_repay(int(params["amount"]))
    else:
        raise ValueError(f"Unsupported policy action '{action}'")


def run_simulation(
    bundle: ContentBundle,
    preset_id: str,
    difficulty_id: str,
    runs: int,
    policy_name: str,
    seed: int,
) -> list[SimulationRunResult]:
    results: list[SimulationRunResult] = []
    for offset in range(runs):
        controller = GameController.new_game(
            bundle=bundle,
            player_name="Sim",
            preset_id=preset_id,
            difficulty_id=difficulty_id,
            seed=seed + offset,
        )
        while controller.state.current_day <= controller.state.total_days and controller.state.game_over_reason is None:
            apply_policy_action(controller, policy_name)
        summary = controller.final_score_summary()
        results.append(
            SimulationRunResult(
                preset_id=preset_id,
                difficulty_id=difficulty_id,
                policy_name=policy_name,
                seed=seed + offset,
                survived=summary.survived_term,
                final_score=summary.final_score,
                ending_cash=controller.state.player.cash,
                ending_bank_balance=controller.state.player.bank_balance,
                ending_debt=controller.state.player.debt,
                ending_stress=controller.state.player.stress,
                ending_energy=controller.state.player.energy,
                ending_gpa=controller.state.player.gpa,
                ending_district_id=controller.state.player.current_district_id,
                game_over_reason=controller.state.game_over_reason,
            )
        )
    return results


def summarize_runs(results: list[SimulationRunResult]) -> dict[str, object]:
    if not results:
        return {"runs": 0}
    failures = Counter(result.game_over_reason or "completed" for result in results)
    grouped_preset: dict[str, list[SimulationRunResult]] = defaultdict(list)
    for result in results:
        grouped_preset[result.preset_id].append(result)
    by_preset = {
        preset_id: {
            "survival_rate": round(sum(1 for result in preset_results if result.survived) / len(preset_results), 4),
            "average_score": round(mean(result.final_score for result in preset_results), 2),
            "average_debt": round(mean(result.ending_debt for result in preset_results), 2),
        }
        for preset_id, preset_results in grouped_preset.items()
    }
    return {
        "runs": len(results),
        "survivals": sum(1 for result in results if result.survived),
        "survival_rate": round(sum(1 for result in results if result.survived) / len(results), 4),
        "average_final_score": round(mean(result.final_score for result in results), 2),
        "average_ending_cash": round(mean(result.ending_cash for result in results), 2),
        "average_ending_bank_balance": round(mean(result.ending_bank_balance for result in results), 2),
        "average_ending_debt": round(mean(result.ending_debt for result in results), 2),
        "average_ending_stress": round(mean(result.ending_stress for result in results), 2),
        "average_ending_energy": round(mean(result.ending_energy for result in results), 2),
        "average_ending_gpa": round(mean(result.ending_gpa for result in results), 3),
        "most_common_game_over_reasons": failures.most_common(3),
        "by_preset": by_preset,
    }
