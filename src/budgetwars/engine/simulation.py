from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from statistics import mean

from budgetwars.models import ContentBundle
from budgetwars.utils.rng import derive_seed

from .game_loop import GameController
from .lookups import get_career_track, get_transport_option


@dataclass(slots=True)
class SimulationRunResult:
    preset_id: str
    difficulty_id: str
    city_id: str
    opening_path_id: str
    policy_name: str
    seed: int
    survived: bool
    final_score: float
    ending_label: str
    game_over_reason: str | None
    ending_cash: int
    ending_savings: int
    ending_debt: int
    ending_stress: int
    ending_energy: int
    final_month: int
    final_career_track_id: str
    final_housing_id: str
    final_transport_id: str


def _career_income_now(bundle: ContentBundle, controller: GameController, career_id: str) -> int:
    track = get_career_track(bundle, career_id)
    city = next(city for city in bundle.cities if city.id == controller.state.player.current_city_id)
    difficulty = next(item for item in bundle.difficulties if item.id == controller.state.difficulty_id)
    return int(round(track.tiers[0].monthly_income * city.career_income_biases.get(career_id, 1.0) * difficulty.income_multiplier))


def conservative_policy(controller: GameController) -> None:
    state = controller.state
    bundle = controller.bundle

    if state.player.stress >= 60 or state.player.energy <= 40:
        if state.player.selected_focus_action_id != "recover":
            controller.change_focus_action("recover")
    elif state.player.education.is_active or state.player.career.track_id in {"trades_apprenticeship", "office_professional"}:
        if state.player.selected_focus_action_id != "push_forward":
            controller.change_focus_action("push_forward")
    else:
        if state.player.selected_focus_action_id != "stack_cash":
            controller.change_focus_action("stack_cash")

    if state.player.debt > 12000 or state.player.cash < 180:
        if state.player.budget_stance_id != "bare_minimum":
            controller.change_budget_stance("bare_minimum")
    elif state.player.debt > 4500 or state.player.savings < 500:
        if state.player.budget_stance_id != "future_focused":
            controller.change_budget_stance("future_focused")
    elif state.player.budget_stance_id != "balanced":
        controller.change_budget_stance("balanced")

    if (
        state.player.current_city_id == "hometown"
        and state.player.family_support >= state.minimum_parent_fallback_support + 5
        and state.player.housing_id != "parents"
        and (state.player.debt > 6000 or state.player.cash < 120)
    ):
        try:
            controller.change_housing("parents")
        except ValueError:
            pass

    if state.player.transport_id == "walk_bike" and state.player.cash + state.player.savings > 1700:
        try:
            controller.change_transport("transit")
        except ValueError:
            pass

    if "college_credential" in state.player.education.earned_credential_ids and state.player.career.track_id != "office_professional":
        try:
            controller.change_career("office_professional")
        except ValueError:
            pass
    elif state.player.debt > 5000 and state.player.career.track_id == "service_retail":
        for target in ("warehouse_logistics", "trades_apprenticeship"):
            try:
                controller.change_career(target)
                break
            except ValueError:
                continue


def ambitious_policy(controller: GameController) -> None:
    state = controller.state
    if state.player.stress >= 75 or state.player.energy <= 25:
        if state.player.selected_focus_action_id != "recover":
            controller.change_focus_action("recover")
    else:
        if state.player.selected_focus_action_id != "stack_cash":
            controller.change_focus_action("stack_cash")

    if state.player.debt > 8000:
        if state.player.budget_stance_id != "bare_minimum":
            controller.change_budget_stance("bare_minimum")
    elif state.player.budget_stance_id != "future_focused":
        controller.change_budget_stance("future_focused")

    if state.player.transport_id in {"walk_bike", "transit"} and state.player.cash + state.player.savings > 1400:
        desired = "beater_car" if state.player.transport_id == "transit" else "transit"
        try:
            controller.change_transport(desired)
        except ValueError:
            pass

    current_income = _career_income_now(controller.bundle, controller, state.player.career.track_id)
    better_tracks = []
    for track in controller.bundle.careers:
        if track.id == state.player.career.track_id:
            continue
        try:
            controller.change_career(track.id)
            better_tracks.append(track.id)
            break
        except ValueError:
            continue
    if better_tracks:
        return

    if current_income < 2400 and state.player.education.program_id == "none":
        for program_id in ("apprenticeship_training", "college"):
            try:
                controller.change_education(program_id)
                break
            except ValueError:
                continue


POLICIES = {
    "conservative": conservative_policy,
    "ambitious": ambitious_policy,
    "balanced": conservative_policy,
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
        policy_name=policy_name,
        seed=seed,
        survived=summary.survived_to_28,
        final_score=summary.final_score,
        ending_label=summary.ending_label,
        game_over_reason=state.game_over_reason,
        ending_cash=state.player.cash,
        ending_savings=state.player.savings,
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
    city_id: str = "hometown",
    opening_path_id: str = "full_time_work",
    policy_name: str = "conservative",
    runs: int = 20,
    seed: int = 42,
) -> list[SimulationRunResult]:
    preset_ids = [preset.id for preset in bundle.presets] if preset_id == "all" else [preset_id]
    results: list[SimulationRunResult] = []
    for chosen_preset in preset_ids:
        for run_index in range(runs):
            run_seed = derive_seed(seed, chosen_preset, difficulty_id, city_id, opening_path_id, policy_name, run_index)
            results.append(
                run_single_simulation(
                    bundle,
                    player_name="Simulator",
                    preset_id=chosen_preset,
                    difficulty_id=difficulty_id,
                    city_id=city_id,
                    opening_path_id=opening_path_id,
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
        "average_ending_debt": round(mean(item.ending_debt for item in results), 2),
        "average_ending_stress": round(mean(item.ending_stress for item in results), 2),
        "average_ending_energy": round(mean(item.ending_energy for item in results), 2),
        "most_common_game_over_reasons": reasons.most_common(3),
        "by_preset": by_preset,
    }


def serialize_run_results(results: list[SimulationRunResult]) -> list[dict[str, object]]:
    return [asdict(result) for result in results]
