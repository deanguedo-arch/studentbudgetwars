from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from statistics import mean

from budgetwars.models import ContentBundle
from budgetwars.utils.rng import derive_seed

from .game_loop import GameController


@dataclass
class SimulationRunResult:
    preset_id: str
    difficulty_id: str
    city_id: str
    opening_path_id: str
    academic_level_id: str
    family_support_level_id: str
    savings_band_id: str
    policy_name: str
    seed: int
    survived: bool
    final_score: float
    ending_label: str
    game_over_reason: str | None
    ending_cash: int
    ending_savings: int
    ending_high_interest_savings: int
    ending_index_fund: int
    ending_growth_fund: int
    ending_debt: int
    ending_stress: int
    ending_energy: int
    final_month: int
    final_career_track_id: str
    final_housing_id: str
    final_transport_id: str


def cautious_policy(controller: GameController) -> None:
    state = controller.state
    if state.player.wealth_strategy_id != "cushion_first" and (
        state.player.debt > 12000 or state.player.cash + state.player.savings < 600
    ):
        controller.change_wealth_strategy("cushion_first")
    elif state.player.wealth_strategy_id != "debt_crusher" and state.player.debt > 18000:
        controller.change_wealth_strategy("debt_crusher")
    if state.player.stress >= 70 or state.player.energy <= 30:
        if state.player.selected_focus_action_id != "recovery_month":
            controller.change_focus_action("recovery_month")
    elif state.player.education.is_active:
        if state.player.selected_focus_action_id != "study_push":
            controller.change_focus_action("study_push")
    else:
        if state.player.selected_focus_action_id != "promotion_hunt":
            controller.change_focus_action("promotion_hunt")

    if state.player.debt > 14000:
        if state.player.budget_stance_id != "aggressive_debt_payoff":
            controller.change_budget_stance("aggressive_debt_payoff")
    elif state.player.cash < 300:
        if state.player.budget_stance_id != "survival":
            controller.change_budget_stance("survival")
    elif state.player.budget_stance_id != "balanced":
        controller.change_budget_stance("balanced")

    if state.player.transport.reliability_score < 45 and state.player.transport_id == "beater_car":
        try:
            controller.change_transport("transit")
        except ValueError:
            pass

    if (
        state.player.current_city_id == "hometown_low_cost"
        and state.player.family_support >= state.minimum_parent_fallback_support + 5
        and state.player.housing_id != "parents"
        and (state.player.debt > 12000 or state.player.cash < 150)
    ):
        try:
            controller.change_housing("parents")
        except ValueError:
            pass

    if state.player.transport_id == "none" and state.player.cash + state.player.savings > 500:
        try:
            controller.change_transport("bike")
        except ValueError:
            pass
    elif state.player.transport_id == "bike" and state.player.cash + state.player.savings > 1100:
        try:
            controller.change_transport("transit")
        except ValueError:
            pass

    if "support_certificate" in state.player.education.earned_credential_ids and state.player.career.track_id != "healthcare_support":
        try:
            controller.change_career("healthcare_support")
        except ValueError:
            pass


def ambitious_policy(controller: GameController) -> None:
    state = controller.state
    if state.player.wealth_strategy_id != "market_chaser" and state.player.debt < 8000 and state.player.cash > 700:
        controller.change_wealth_strategy("market_chaser")
    elif state.player.debt > 20000 and state.player.wealth_strategy_id != "debt_crusher":
        controller.change_wealth_strategy("debt_crusher")
    if state.player.stress >= 82 or state.player.energy <= 20:
        if state.player.selected_focus_action_id != "recovery_month":
            controller.change_focus_action("recovery_month")
    elif state.player.education.is_active and state.player.education.program_id in {"part_time_college", "full_time_university"}:
        if state.player.selected_focus_action_id != "study_push":
            controller.change_focus_action("study_push")
    else:
        if state.player.selected_focus_action_id != "overtime":
            controller.change_focus_action("overtime")

    if state.player.debt > 22000:
        if state.player.budget_stance_id != "survival":
            controller.change_budget_stance("survival")
    elif state.player.monthly_surplus < 0:
        if state.player.budget_stance_id != "aggressive_debt_payoff":
            controller.change_budget_stance("aggressive_debt_payoff")
    elif state.player.budget_stance_id != "quality_of_life":
        controller.change_budget_stance("quality_of_life")

    if state.player.transport_id in {"none", "bike"} and state.player.cash + state.player.savings > 1500:
        desired = "transit" if state.player.transport_id == "none" else "beater_car"
        try:
            controller.change_transport(desired)
        except ValueError:
            pass

    for target in ("sales", "warehouse_logistics", "office_admin", "degree_gated_professional"):
        try:
            controller.change_career(target)
            break
        except ValueError:
            continue

    if state.player.education.program_id == "none" and state.player.academic_strength >= 60 and state.player.cash < 800:
        for program_id in ("part_time_college", "certificate", "upgrading"):
            try:
                controller.change_education(program_id)
                break
            except ValueError:
                continue
    if (
        state.player.housing_id == "parents"
        and state.current_month > 24
        and state.player.cash + state.player.savings > 1400
        and state.player.family_support < state.minimum_parent_fallback_support + 12
    ):
        try:
            controller.change_housing("roommates")
        except ValueError:
            pass


POLICIES = {
    "cautious": cautious_policy,
    "ambitious": ambitious_policy,
}


def apply_policy_action(controller: GameController, policy_name: str) -> None:
    if policy_name not in POLICIES:
        raise ValueError(f"Unknown policy: {policy_name}")
    POLICIES[policy_name](controller)
    controller.resolve_month()


def run_single_simulation(
    bundle: ContentBundle,
    *,
    player_name: str,
    preset_id: str,
    difficulty_id: str,
    city_id: str,
    opening_path_id: str,
    academic_level_id: str,
    family_support_level_id: str,
    savings_band_id: str,
    policy_name: str,
    seed: int,
) -> SimulationRunResult:
    controller = GameController.new_game(
        bundle,
        player_name=player_name,
        preset_id=preset_id,
        difficulty_id=difficulty_id,
        seed=seed,
        city_id=city_id,
        opening_path_id=opening_path_id,
        academic_level_id=academic_level_id,
        family_support_level_id=family_support_level_id,
        savings_band_id=savings_band_id,
    )
    while not controller.is_finished():
        apply_policy_action(controller, policy_name)
    summary = controller.final_score_summary()
    state = controller.state
    return SimulationRunResult(
        preset_id=preset_id,
        difficulty_id=difficulty_id,
        city_id=city_id,
        opening_path_id=opening_path_id,
        academic_level_id=academic_level_id,
        family_support_level_id=family_support_level_id,
        savings_band_id=savings_band_id,
        policy_name=policy_name,
        seed=seed,
        survived=summary.survived_to_28,
        final_score=summary.final_score,
        ending_label=summary.ending_label,
        game_over_reason=state.game_over_reason,
        ending_cash=state.player.cash,
        ending_savings=state.player.savings,
        ending_high_interest_savings=state.player.high_interest_savings,
        ending_index_fund=state.player.index_fund,
        ending_growth_fund=state.player.aggressive_growth_fund,
        ending_debt=state.player.debt,
        ending_stress=state.player.stress,
        ending_energy=state.player.energy,
        final_month=state.current_month,
        final_career_track_id=state.player.career.track_id,
        final_housing_id=state.player.housing_id,
        final_transport_id=state.player.transport_id,
    )


def run_simulation(
    bundle: ContentBundle,
    *,
    preset_id: str = "all",
    difficulty_id: str = "normal",
    city_id: str = "mid_size_city",
    opening_path_id: str = "full_time_work",
    academic_level_id: str = "average",
    family_support_level_id: str = "medium",
    savings_band_id: str = "some",
    policy_name: str = "cautious",
    runs: int = 20,
    seed: int = 42,
) -> list[SimulationRunResult]:
    preset_ids = [preset.id for preset in bundle.presets] if preset_id == "all" else [preset_id]
    results: list[SimulationRunResult] = []
    for chosen_preset in preset_ids:
        for run_index in range(runs):
            run_seed = derive_seed(
                seed,
                chosen_preset,
                difficulty_id,
                city_id,
                opening_path_id,
                academic_level_id,
                family_support_level_id,
                savings_band_id,
                policy_name,
                run_index,
            )
            results.append(
                run_single_simulation(
                    bundle,
                    player_name="Simulator",
                    preset_id=chosen_preset,
                    difficulty_id=difficulty_id,
                    city_id=city_id,
                    opening_path_id=opening_path_id,
                    academic_level_id=academic_level_id,
                    family_support_level_id=family_support_level_id,
                    savings_band_id=savings_band_id,
                    policy_name=policy_name,
                    seed=run_seed,
                )
            )
    return results


def summarize_runs(results: list[SimulationRunResult]) -> dict[str, object]:
    if not results:
        return {"runs": 0}

    survivals = [result for result in results if result.survived]
    reasons = Counter(result.game_over_reason or "survived" for result in results)
    by_preset: dict[str, dict[str, float]] = {}
    for preset_id in sorted({result.preset_id for result in results}):
        subset = [result for result in results if result.preset_id == preset_id]
        by_preset[preset_id] = {
            "survival_rate": round(len([item for item in subset if item.survived]) / len(subset), 3),
            "average_score": round(mean(item.final_score for item in subset), 2),
            "average_debt": round(mean(item.ending_debt for item in subset), 2),
        }
    return {
        "runs": len(results),
        "survivals": len(survivals),
        "survival_rate": round(len(survivals) / len(results), 3),
        "average_final_score": round(mean(item.final_score for item in results), 2),
        "average_ending_cash": round(mean(item.ending_cash for item in results), 2),
        "average_ending_savings": round(mean(item.ending_savings for item in results), 2),
        "average_ending_high_interest_savings": round(mean(item.ending_high_interest_savings for item in results), 2),
        "average_ending_index_fund": round(mean(item.ending_index_fund for item in results), 2),
        "average_ending_growth_fund": round(mean(item.ending_growth_fund for item in results), 2),
        "average_ending_debt": round(mean(item.ending_debt for item in results), 2),
        "average_ending_stress": round(mean(item.ending_stress for item in results), 2),
        "average_ending_energy": round(mean(item.ending_energy for item in results), 2),
        "most_common_game_over_reasons": reasons.most_common(3),
        "by_preset": by_preset,
    }


def serialize_run_results(results: list[SimulationRunResult]) -> list[dict[str, object]]:
    return [asdict(result) for result in results]
