from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
import csv
import json

from .game import advance_week, check_game_over, start_new_game
from .jobs import get_job, switch_job
from .locations import move_location
from .models import ContentBundle, EventDefinition, ExpenseDefinition, GameState, JobDefinition, StatEffects
from .scoring import calculate_final_score
from .utils import clamp


@dataclass(frozen=True)
class SimulationRunResult:
    preset_id: str
    difficulty_id: str
    policy_name: str
    seed: int
    survived_term: bool
    final_score: float
    ending_cash: int
    ending_savings: int
    ending_debt: int
    ending_stress: int
    ending_energy: int
    weeks_played: int
    game_over_reason: str | None
    starting_job_id: str | None
    ending_job_id: str | None


@dataclass(frozen=True)
class SimulationPolicy:
    name: str
    description: str
    choose_location: Callable[[GameState, ContentBundle], str | None]
    choose_weekly_action: Callable[[GameState, ContentBundle], str]
    should_pay_optional_expense: Callable[[GameState, ExpenseDefinition, ContentBundle], bool]
    choose_event_choice: Callable[[GameState, EventDefinition, ContentBundle], str | None]
    choose_job_switch: Callable[[GameState, ContentBundle], str | None]


def _sum_temporary_effects(temporary_effects: list[object]) -> StatEffects:
    projected: StatEffects = {}
    for effect in temporary_effects:
        duration = getattr(effect, "duration_weeks", 1)
        for key, value in getattr(effect, "effects", {}).items():
            projected[key] = projected.get(key, 0) + (value * duration)
    return projected


def _merge_effects(*effect_maps: StatEffects) -> StatEffects:
    merged: StatEffects = {}
    for effect_map in effect_maps:
        for key, value in effect_map.items():
            merged[key] = merged.get(key, 0) + value
    return merged


def _project_player_values(state: GameState, effects: StatEffects) -> dict[str, int]:
    projected = {
        "cash": state.player.cash,
        "savings": state.player.savings,
        "debt": state.player.debt,
        "stress": state.player.stress,
        "energy": state.player.energy,
    }
    for key, delta in effects.items():
        if key in projected:
            projected[key] += delta
    projected["stress"] = clamp(projected["stress"], 0, state.max_stress)
    projected["energy"] = clamp(projected["energy"], 0, state.max_energy)
    return projected


def _score_projected_state(
    state: GameState,
    effects: StatEffects,
    *,
    cash_weight: float,
    savings_weight: float,
    debt_weight: float,
    stress_weight: float,
    energy_weight: float,
) -> float:
    projected = _project_player_values(state, effects)
    score = (
        projected["cash"] * cash_weight
        + projected["savings"] * savings_weight
        + projected["debt"] * debt_weight
        + projected["stress"] * stress_weight
        + projected["energy"] * energy_weight
    )
    if projected["energy"] <= state.low_energy_threshold:
        score -= 25.0
    if projected["stress"] >= state.max_stress - 8:
        score -= 30.0
    if projected["debt"] >= int(state.debt_game_over_threshold * 0.9):
        score -= 35.0
    return score


def _payment_effects_for_expense(state: GameState, amount: int) -> StatEffects:
    cash_used = min(state.player.cash, amount)
    remaining = amount - cash_used
    savings_used = min(state.player.savings, remaining)
    remaining -= savings_used

    effects: StatEffects = {}
    if cash_used:
        effects["cash"] = -cash_used
    if savings_used:
        effects["savings"] = -savings_used
    if remaining:
        effects["debt"] = remaining
    return effects


def _weekly_income(job: JobDefinition) -> int:
    return job.hourly_pay * job.hours_per_week


def _strain_score(job: JobDefinition) -> int:
    return job.energy_cost + max(job.stress_delta, 0) * 2


def _choose_low_impact_job(jobs: list[JobDefinition]) -> JobDefinition:
    return min(jobs, key=lambda job: (_strain_score(job), _weekly_income(job)))


def _choose_high_income_job(jobs: list[JobDefinition]) -> JobDefinition:
    return max(jobs, key=lambda job: (_weekly_income(job), -_strain_score(job)))


def _location_recovery_score(modifiers: dict[str, int]) -> float:
    stress_relief = -modifiers.get("stress", 0)
    energy_relief = modifiers.get("energy", 0)
    cash_pressure = modifiers.get("cash", 0)
    return float(stress_relief + energy_relief + (cash_pressure / 3.0))


def _choose_recovery_location(bundle: ContentBundle) -> str:
    return max(bundle.locations, key=lambda location: _location_recovery_score(location.modifiers)).id


def _balanced_choose_location(state: GameState, bundle: ContentBundle) -> str | None:
    current_job = get_job(bundle.jobs, state.player.job_id)
    if current_job is None:
        return None

    if state.player.energy <= state.low_energy_threshold + 4 or state.player.stress >= state.max_stress - 10:
        target_id = _choose_recovery_location(bundle)
        return target_id if target_id != state.player.location_id else None

    if (
        state.player.debt >= int(state.debt_game_over_threshold * 0.70)
        and state.player.energy >= state.low_energy_threshold + 9
        and state.player.stress <= state.max_stress - 18
        and state.player.location_id != current_job.location_id
    ):
        return current_job.location_id

    if (
        state.player.location_id != current_job.location_id
        and (bundle.config.offsite_work_energy_penalty >= 3 or bundle.config.offsite_work_stress_penalty >= 2)
        and state.player.energy <= state.low_energy_threshold + 10
    ):
        return current_job.location_id

    return None


def _balanced_choose_action(state: GameState, bundle: ContentBundle) -> str:
    if state.player.energy <= max(state.low_energy_threshold + 6, 24):
        return "rest"
    if state.player.stress >= state.max_stress - 14:
        return "rest"
    if state.player.debt >= int(state.debt_game_over_threshold * 0.75) and state.player.energy >= 35:
        return "work"
    return "work"


def _balanced_should_pay_optional_expense(
    state: GameState,
    expense: ExpenseDefinition,
    bundle: ContentBundle,
) -> bool:
    liquid_funds = state.player.cash + state.player.savings
    if liquid_funds < expense.amount:
        return False

    pay_effects = _merge_effects(
        _payment_effects_for_expense(state, expense.amount),
        expense.pay_effects,
        _sum_temporary_effects(expense.pay_temporary_effects),
    )
    skip_effects = _merge_effects(
        expense.skip_effects,
        _sum_temporary_effects(expense.skip_temporary_effects),
    )

    pay_score = _score_projected_state(
        state,
        pay_effects,
        cash_weight=0.10,
        savings_weight=0.14,
        debt_weight=-0.20,
        stress_weight=-1.20,
        energy_weight=0.95,
    )
    skip_score = _score_projected_state(
        state,
        skip_effects,
        cash_weight=0.10,
        savings_weight=0.14,
        debt_weight=-0.20,
        stress_weight=-1.20,
        energy_weight=0.95,
    )
    return pay_score >= skip_score


def _balanced_choose_event_choice(
    state: GameState,
    event: EventDefinition,
    bundle: ContentBundle,
) -> str | None:
    if not event.choices:
        return None

    best_choice = event.choices[0]
    best_score = float("-inf")
    for choice in event.choices:
        combined_effects = _merge_effects(
            event.effects,
            choice.effects,
            _sum_temporary_effects(event.temporary_effects),
            _sum_temporary_effects(choice.temporary_effects),
        )
        score = _score_projected_state(
            state,
            combined_effects,
            cash_weight=0.10,
            savings_weight=0.14,
            debt_weight=-0.21,
            stress_weight=-1.20,
            energy_weight=0.95,
        )
        if score > best_score:
            best_choice = choice
            best_score = score
    return best_choice.id


def _balanced_choose_job_switch(state: GameState, bundle: ContentBundle) -> str | None:
    current_job = get_job(bundle.jobs, state.player.job_id)
    if current_job is None:
        return None

    if state.player.stress + bundle.config.job_switch_stress_penalty >= state.max_stress:
        return None

    target_job: JobDefinition | None = None
    if state.player.energy <= state.low_energy_threshold + 3 or state.player.stress >= state.max_stress - 10:
        target_job = _choose_low_impact_job(bundle.jobs)
    elif (
        state.player.debt >= int(state.debt_game_over_threshold * 0.70)
        and state.player.energy >= state.low_energy_threshold + 12
        and state.player.stress <= state.max_stress - 20
    ):
        target_job = _choose_high_income_job(bundle.jobs)

    if target_job is None or target_job.id == current_job.id:
        return None
    return target_job.id


def _cash_hungry_choose_action(state: GameState, bundle: ContentBundle) -> str:
    if state.player.energy <= state.low_energy_threshold or state.player.stress >= state.max_stress - 6:
        return "rest"
    return "work"


def _cash_hungry_choose_location(state: GameState, bundle: ContentBundle) -> str | None:
    current_job = get_job(bundle.jobs, state.player.job_id)
    if current_job is None:
        return None

    if state.player.energy <= state.low_energy_threshold or state.player.stress >= state.max_stress - 6:
        target_id = _choose_recovery_location(bundle)
        return target_id if target_id != state.player.location_id else None

    if state.player.location_id != current_job.location_id:
        return current_job.location_id

    return None


def _cash_hungry_should_pay_optional_expense(
    state: GameState,
    expense: ExpenseDefinition,
    bundle: ContentBundle,
) -> bool:
    liquid_funds = state.player.cash + state.player.savings
    if liquid_funds < expense.amount:
        return False

    pay_effects = _merge_effects(
        _payment_effects_for_expense(state, expense.amount),
        expense.pay_effects,
        _sum_temporary_effects(expense.pay_temporary_effects),
    )
    skip_effects = _merge_effects(
        expense.skip_effects,
        _sum_temporary_effects(expense.skip_temporary_effects),
    )

    pay_score = _score_projected_state(
        state,
        pay_effects,
        cash_weight=0.22,
        savings_weight=0.10,
        debt_weight=-0.30,
        stress_weight=-0.80,
        energy_weight=0.45,
    )
    skip_score = _score_projected_state(
        state,
        skip_effects,
        cash_weight=0.22,
        savings_weight=0.10,
        debt_weight=-0.30,
        stress_weight=-0.80,
        energy_weight=0.45,
    )
    return pay_score >= skip_score


def _cash_hungry_choose_event_choice(
    state: GameState,
    event: EventDefinition,
    bundle: ContentBundle,
) -> str | None:
    if not event.choices:
        return None

    best_choice = event.choices[0]
    best_score = float("-inf")
    for choice in event.choices:
        combined_effects = _merge_effects(
            event.effects,
            choice.effects,
            _sum_temporary_effects(event.temporary_effects),
            _sum_temporary_effects(choice.temporary_effects),
        )
        score = _score_projected_state(
            state,
            combined_effects,
            cash_weight=0.22,
            savings_weight=0.10,
            debt_weight=-0.31,
            stress_weight=-0.75,
            energy_weight=0.40,
        )
        if score > best_score:
            best_choice = choice
            best_score = score
    return best_choice.id


def _cash_hungry_choose_job_switch(state: GameState, bundle: ContentBundle) -> str | None:
    current_job = get_job(bundle.jobs, state.player.job_id)
    if current_job is None:
        return None

    if state.player.stress + bundle.config.job_switch_stress_penalty >= state.max_stress:
        return None

    highest_income = _choose_high_income_job(bundle.jobs)
    lowest_strain = _choose_low_impact_job(bundle.jobs)

    if (
        state.player.debt >= int(state.debt_game_over_threshold * 0.55)
        and state.player.energy >= state.low_energy_threshold + 8
        and state.player.stress <= state.max_stress - 16
        and highest_income.id != current_job.id
    ):
        return highest_income.id

    if (
        state.player.energy <= state.low_energy_threshold
        or state.player.stress >= state.max_stress - 7
    ) and lowest_strain.id != current_job.id:
        return lowest_strain.id

    return None


POLICIES: dict[str, SimulationPolicy] = {
    "balanced": SimulationPolicy(
        name="balanced",
        description="Tries to stay solvent while avoiding collapse from stress and energy pressure.",
        choose_location=_balanced_choose_location,
        choose_weekly_action=_balanced_choose_action,
        should_pay_optional_expense=_balanced_should_pay_optional_expense,
        choose_event_choice=_balanced_choose_event_choice,
        choose_job_switch=_balanced_choose_job_switch,
    ),
    "cash_hungry": SimulationPolicy(
        name="cash_hungry",
        description="Prioritizes cashflow and debt pressure, tolerating higher personal strain.",
        choose_location=_cash_hungry_choose_location,
        choose_weekly_action=_cash_hungry_choose_action,
        should_pay_optional_expense=_cash_hungry_should_pay_optional_expense,
        choose_event_choice=_cash_hungry_choose_event_choice,
        choose_job_switch=_cash_hungry_choose_job_switch,
    ),
}


def get_policy(policy_name: str) -> SimulationPolicy:
    policy = POLICIES.get(policy_name)
    if policy is None:
        valid = ", ".join(sorted(POLICIES))
        raise ValueError(f"Unknown policy '{policy_name}'. Available policies: {valid}")
    return policy


def simulate_term(
    bundle: ContentBundle,
    *,
    preset_id: str,
    difficulty_id: str,
    seed: int,
    policy_name: str,
) -> SimulationRunResult:
    policy = get_policy(policy_name)
    _, state = start_new_game(
        preset_id=preset_id,
        difficulty_id=difficulty_id,
        seed=seed,
        bundle=bundle,
    )
    starting_job_id = state.player.job_id

    while not check_game_over(state):
        target_job_id = policy.choose_job_switch(state, bundle)
        if target_job_id:
            state = switch_job(
                state,
                bundle.jobs,
                target_job_id,
                stress_penalty=bundle.config.job_switch_stress_penalty,
                sync_location_to_job=True,
            )

        target_location_id = policy.choose_location(state, bundle)
        if target_location_id:
            state = move_location(
                state,
                bundle.locations,
                target_location_id,
                stress_penalty=bundle.config.location_move_stress_penalty,
            )

        week_snapshot = state
        weekly_action = policy.choose_weekly_action(week_snapshot, bundle)
        state = advance_week(
            state,
            bundle,
            action=weekly_action,
            optional_expense_resolver=lambda expense, snapshot=week_snapshot: policy.should_pay_optional_expense(
                snapshot, expense, bundle
            ),
            choice_resolver=lambda event, snapshot=week_snapshot: policy.choose_event_choice(snapshot, event, bundle),
        )

    score = calculate_final_score(state, bundle.scoring)
    return SimulationRunResult(
        preset_id=preset_id,
        difficulty_id=difficulty_id,
        policy_name=policy.name,
        seed=seed,
        survived_term=score.survived_term,
        final_score=score.final_score,
        ending_cash=state.player.cash,
        ending_savings=state.player.savings,
        ending_debt=state.player.debt,
        ending_stress=state.player.stress,
        ending_energy=state.player.energy,
        weeks_played=max(0, state.current_week - 1),
        game_over_reason=state.game_over_reason,
        starting_job_id=starting_job_id,
        ending_job_id=state.player.job_id,
    )


def run_simulation_batch(
    bundle: ContentBundle,
    *,
    preset_ids: list[str],
    difficulty_id: str,
    runs_per_preset: int,
    policy_name: str,
    seed: int | None = None,
) -> list[SimulationRunResult]:
    if runs_per_preset <= 0:
        raise ValueError("runs_per_preset must be greater than zero")
    if not preset_ids:
        raise ValueError("preset_ids must include at least one preset id")

    base_seed = bundle.config.default_seed if seed is None else seed
    results: list[SimulationRunResult] = []
    for preset_index, preset_id in enumerate(preset_ids):
        for run_index in range(runs_per_preset):
            run_seed = base_seed + (preset_index * 100_000) + run_index
            results.append(
                simulate_term(
                    bundle,
                    preset_id=preset_id,
                    difficulty_id=difficulty_id,
                    seed=run_seed,
                    policy_name=policy_name,
                )
            )
    return results


def _summarize_group(results: list[SimulationRunResult]) -> dict[str, float | int]:
    runs = len(results)
    successes = sum(1 for result in results if result.survived_term)
    return {
        "runs": runs,
        "successes": successes,
        "survival_rate": successes / runs if runs else 0.0,
        "avg_final_score": sum(result.final_score for result in results) / runs if runs else 0.0,
        "avg_ending_cash": sum(result.ending_cash for result in results) / runs if runs else 0.0,
        "avg_ending_savings": sum(result.ending_savings for result in results) / runs if runs else 0.0,
        "avg_ending_debt": sum(result.ending_debt for result in results) / runs if runs else 0.0,
        "avg_ending_stress": sum(result.ending_stress for result in results) / runs if runs else 0.0,
        "avg_ending_energy": sum(result.ending_energy for result in results) / runs if runs else 0.0,
    }


def build_balance_audit(results: list[SimulationRunResult]) -> dict[str, object]:
    overall = _summarize_group(results)
    failure_counts = Counter(result.game_over_reason for result in results if not result.survived_term)
    most_common_failures = [
        {"reason": reason, "count": count}
        for reason, count in failure_counts.most_common(5)
    ]

    by_preset_map: dict[str, list[SimulationRunResult]] = defaultdict(list)
    by_starting_job_map: dict[str, list[SimulationRunResult]] = defaultdict(list)
    for result in results:
        by_preset_map[result.preset_id].append(result)
        by_starting_job_map[result.starting_job_id or "none"].append(result)

    by_preset = {
        preset_id: _summarize_group(group)
        for preset_id, group in sorted(by_preset_map.items())
    }
    by_starting_job = {
        job_id: _summarize_group(group)
        for job_id, group in sorted(by_starting_job_map.items())
    }

    alerts: list[str] = []
    survival_rates = [float(summary["survival_rate"]) for summary in by_preset.values()]
    if survival_rates:
        spread = max(survival_rates) - min(survival_rates)
        if spread >= 0.35:
            alerts.append(
                f"Large preset survival spread detected ({spread:.1%}); one preset may be dramatically easier."
            )
        if min(survival_rates) < 0.10:
            alerts.append("At least one preset survives under 10% of runs and may be too punishing.")

    return {
        "overall": overall,
        "most_common_game_over_reasons": most_common_failures,
        "by_preset": by_preset,
        "by_starting_job": by_starting_job,
        "alerts": alerts,
    }


def format_balance_audit(audit: dict[str, object]) -> str:
    overall = audit["overall"]
    assert isinstance(overall, dict)
    lines = [
        "Simulation Summary",
        f"- runs: {int(overall['runs'])}",
        f"- survivals: {int(overall['successes'])}",
        f"- survival_rate: {float(overall['survival_rate']):.1%}",
        f"- avg_final_score: {float(overall['avg_final_score']):.2f}",
        f"- avg_ending_cash: {float(overall['avg_ending_cash']):.2f}",
        f"- avg_ending_savings: {float(overall['avg_ending_savings']):.2f}",
        f"- avg_ending_debt: {float(overall['avg_ending_debt']):.2f}",
        f"- avg_ending_stress: {float(overall['avg_ending_stress']):.2f}",
        f"- avg_ending_energy: {float(overall['avg_ending_energy']):.2f}",
    ]

    lines.append("Most Common Game-Over Reasons")
    reasons = audit["most_common_game_over_reasons"]
    assert isinstance(reasons, list)
    if reasons:
        for reason in reasons:
            assert isinstance(reason, dict)
            lines.append(f"- {reason['reason']}: {reason['count']}")
    else:
        lines.append("- none")

    lines.append("By Preset")
    preset_rows = audit["by_preset"]
    assert isinstance(preset_rows, dict)
    for preset_id, summary in preset_rows.items():
        assert isinstance(summary, dict)
        lines.append(
            f"- {preset_id}: survival {float(summary['survival_rate']):.1%}, "
            f"avg_score {float(summary['avg_final_score']):.2f}, "
            f"avg_debt {float(summary['avg_ending_debt']):.2f}"
        )

    lines.append("By Starting Job")
    job_rows = audit["by_starting_job"]
    assert isinstance(job_rows, dict)
    for job_id, summary in job_rows.items():
        assert isinstance(summary, dict)
        lines.append(
            f"- {job_id}: survival {float(summary['survival_rate']):.1%}, "
            f"avg_score {float(summary['avg_final_score']):.2f}, "
            f"avg_debt {float(summary['avg_ending_debt']):.2f}"
        )

    alerts = audit["alerts"]
    assert isinstance(alerts, list)
    lines.append("Balance Alerts")
    if alerts:
        for alert in alerts:
            lines.append(f"- {alert}")
    else:
        lines.append("- none")
    return "\n".join(lines)


def write_json_report(
    path: Path,
    *,
    audit: dict[str, object],
    results: list[SimulationRunResult],
) -> None:
    payload = {
        "audit": audit,
        "results": [asdict(result) for result in results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv_report(path: Path, *, results: list[SimulationRunResult]) -> None:
    if not results:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))
