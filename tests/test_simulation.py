import math

import pytest

from budgetwars.game import check_game_over, start_new_game
from budgetwars.loaders import load_all_content
from budgetwars.simulation import (
    build_balance_audit,
    get_policy,
    run_simulation_batch,
    write_csv_report,
    write_json_report,
)


def _weekly_income(job) -> int:
    return job.hourly_pay * job.hours_per_week


def test_simulation_runner_completes_small_batch_and_reports_metrics() -> None:
    bundle = load_all_content()
    results = run_simulation_batch(
        bundle,
        preset_ids=["default_student"],
        difficulty_id="normal",
        runs_per_preset=3,
        policy_name="balanced",
        seed=700,
    )

    assert len(results) == 3
    audit = build_balance_audit(results)
    overall = audit["overall"]
    assert isinstance(overall, dict)
    assert overall["runs"] == 3
    assert "survival_rate" in overall
    assert "avg_final_score" in overall
    assert "avg_ending_debt" in overall
    assert "most_common_game_over_reasons" in audit


def test_simulation_is_deterministic_for_same_seed() -> None:
    bundle = load_all_content()
    first = run_simulation_batch(
        bundle,
        preset_ids=["default_student", "commuter_student"],
        difficulty_id="normal",
        runs_per_preset=2,
        policy_name="balanced",
        seed=1337,
    )
    second = run_simulation_batch(
        bundle,
        preset_ids=["default_student", "commuter_student"],
        difficulty_id="normal",
        runs_per_preset=2,
        policy_name="balanced",
        seed=1337,
    )

    assert [
        (result.seed, result.survived_term, result.final_score, result.ending_debt, result.game_over_reason)
        for result in first
    ] == [
        (result.seed, result.survived_term, result.final_score, result.ending_debt, result.game_over_reason)
        for result in second
    ]


def test_unknown_policy_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown policy"):
        get_policy("missing_policy")


def test_presets_do_not_start_in_immediate_game_over_state() -> None:
    bundle = load_all_content()
    for preset in bundle.presets:
        _, state = start_new_game(bundle=bundle, preset_id=preset.id, seed=99)
        assert check_game_over(state) is False


def test_optional_expenses_have_distinct_pay_and_skip_tradeoffs() -> None:
    bundle = load_all_content()
    optional_expenses = [expense for expense in bundle.expenses if not expense.mandatory]
    assert optional_expenses

    for expense in optional_expenses:
        pay_signature = (
            tuple(sorted(expense.pay_effects.items())),
            tuple(
                (effect.id, effect.duration_weeks, tuple(sorted(effect.effects.items())))
                for effect in expense.pay_temporary_effects
            ),
        )
        skip_signature = (
            tuple(sorted(expense.skip_effects.items())),
            tuple(
                (effect.id, effect.duration_weeks, tuple(sorted(effect.effects.items())))
                for effect in expense.skip_temporary_effects
            ),
        )
        assert pay_signature != skip_signature


def test_high_income_jobs_show_at_least_one_cost_tradeoff() -> None:
    bundle = load_all_content()
    ranked_jobs = sorted(bundle.jobs, key=_weekly_income)
    lowest_income = ranked_jobs[0]
    highest_income = ranked_jobs[-1]

    assert _weekly_income(highest_income) >= _weekly_income(lowest_income)
    assert (
        highest_income.energy_cost >= lowest_income.energy_cost
        or highest_income.stress_delta >= lowest_income.stress_delta
        or highest_income.hours_per_week <= lowest_income.hours_per_week
    )


def test_simulation_aggregate_rates_are_sane_numbers() -> None:
    bundle = load_all_content()
    results = run_simulation_batch(
        bundle,
        preset_ids=[preset.id for preset in bundle.presets],
        difficulty_id="normal",
        runs_per_preset=1,
        policy_name="cash_hungry",
        seed=21,
    )
    audit = build_balance_audit(results)
    overall = audit["overall"]
    assert isinstance(overall, dict)
    assert 0.0 <= float(overall["survival_rate"]) <= 1.0
    assert math.isfinite(float(overall["avg_final_score"]))


def test_simulation_reports_can_be_written_to_files(tmp_path) -> None:
    bundle = load_all_content()
    results = run_simulation_batch(
        bundle,
        preset_ids=["default_student"],
        difficulty_id="normal",
        runs_per_preset=1,
        policy_name="balanced",
        seed=500,
    )
    audit = build_balance_audit(results)
    json_path = tmp_path / "report.json"
    csv_path = tmp_path / "report.csv"

    write_json_report(json_path, audit=audit, results=results)
    write_csv_report(csv_path, results=results)

    assert json_path.exists()
    assert csv_path.exists()
    assert "overall" in json_path.read_text(encoding="utf-8")
