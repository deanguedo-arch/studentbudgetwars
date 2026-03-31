from __future__ import annotations

from budgetwars.engine import run_simulation, summarize_runs


def test_simulation_runner_is_deterministic(bundle):
    first = run_simulation(bundle, preset_id="dorm_flipper", difficulty_id="normal", runs=2, policy_name="balanced", seed=99)
    second = run_simulation(bundle, preset_id="dorm_flipper", difficulty_id="normal", runs=2, policy_name="balanced", seed=99)
    assert first == second


def test_simulation_summary_reports_core_metrics(bundle):
    results = run_simulation(bundle, preset_id="scholarship_grinder", difficulty_id="normal", runs=2, policy_name="balanced", seed=123)
    summary = summarize_runs(results)
    assert summary["runs"] == 2
    assert "survival_rate" in summary
    assert "average_final_score" in summary
    assert "by_preset" in summary
