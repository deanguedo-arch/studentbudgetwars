from __future__ import annotations

from budgetwars.engine.simulation import run_simulation, summarize_runs


def test_simulation_is_deterministic(bundle):
    first = run_simulation(
        bundle,
        preset_id="supported_student",
        difficulty_id="easy",
        city_id="hometown",
        opening_path_id="full_time_work",
        policy_name="conservative",
        runs=2,
        seed=99,
    )
    second = run_simulation(
        bundle,
        preset_id="supported_student",
        difficulty_id="easy",
        city_id="hometown",
        opening_path_id="full_time_work",
        policy_name="conservative",
        runs=2,
        seed=99,
    )
    assert [item.final_score for item in first] == [item.final_score for item in second]
    assert summarize_runs(first) == summarize_runs(second)


def test_conservative_policy_can_finish_a_full_run(bundle):
    result = run_simulation(
        bundle,
        preset_id="supported_student",
        difficulty_id="easy",
        city_id="hometown",
        opening_path_id="full_time_work",
        policy_name="conservative",
        runs=1,
        seed=7,
    )[0]
    assert result.survived is True
    assert result.final_month == 121


def test_ambitious_policy_can_finish_a_full_run(bundle):
    result = run_simulation(
        bundle,
        preset_id="broke_but_ambitious",
        difficulty_id="easy",
        city_id="hometown",
        opening_path_id="full_time_work",
        policy_name="ambitious",
        runs=1,
        seed=11,
    )[0]
    assert result.survived is True
    assert result.final_month == 121
