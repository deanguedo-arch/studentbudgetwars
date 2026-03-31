from budgetwars.budget import apply_weekly_expenses, apply_weekly_income
from budgetwars.events import resolve_event_choice
from budgetwars.game import advance_week, check_game_over, start_new_game
from budgetwars.loaders import load_all_content
from budgetwars.scoring import calculate_final_score


def test_weekly_expenses_reduce_cash_then_savings_exactly() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=1)
    state = state.model_copy(
        update={"player": state.player.model_copy(update={"cash": 300, "savings": 50, "debt": 100})}
    )

    updated = apply_weekly_expenses(state, bundle.expenses, expense_multiplier=1.0)

    assert updated.player.cash == 0
    assert updated.player.savings == 47
    assert updated.player.debt == 100
    assert updated.missed_essential_weeks == 0


def test_essentials_fall_to_debt_when_funds_are_short() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=2)
    state = state.model_copy(
        update={
            "player": state.player.model_copy(update={"cash": 50, "savings": 10, "debt": 100}),
            "missed_essential_weeks": 0,
        }
    )

    updated = apply_weekly_expenses(state, bundle.expenses, expense_multiplier=1.0)

    assert updated.player.cash == 0
    assert updated.player.savings == 0
    assert updated.player.debt == 343
    assert updated.missed_essential_weeks == 1


def test_weekly_income_applies_expected_job_math() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=3)
    job = next(job for job in bundle.jobs if job.id == "library_assistant")

    updated = apply_weekly_income(state, job, income_multiplier=1.0, stress_multiplier=1.0)

    assert updated.player.cash == state.player.cash + 150
    assert updated.player.energy == state.player.energy - 12
    assert updated.player.stress == state.player.stress + 2


def test_rest_action_changes_stress_and_energy_correctly() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=4)
    state = state.model_copy(update={"player": state.player.model_copy(update={"debt": 0})})
    quiet_bundle = bundle.model_copy(
        update={
            "expenses": [],
            "config": bundle.config.model_copy(
                update={"weekly_event_chance": 0.0, "debt_interest_rate": 0.0, "overdraft_fee": 0}
            ),
        }
    )

    updated = advance_week(state, quiet_bundle, action="rest")

    assert updated.player.energy == 93
    assert updated.player.stress == 10
    assert updated.current_week == state.current_week + 1


def test_event_choice_application_changes_stats_correctly() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=5)
    event = next(event for event in bundle.events if event.id == "unexpected_textbook_cost")

    updated = resolve_event_choice(state, event, "put_on_credit")

    assert updated.player.debt == state.player.debt + 55
    assert updated.player.stress == state.player.stress + 10


def test_low_energy_streak_triggers_game_over() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=6)
    state = state.model_copy(update={"consecutive_low_energy_weeks": state.low_energy_week_limit})

    assert check_game_over(state) is True


def test_debt_threshold_triggers_game_over() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=7)
    state = state.model_copy(update={"player": state.player.model_copy(update={"debt": state.debt_game_over_threshold})})

    assert check_game_over(state) is True


def test_final_scoring_returns_survive_and_fail_outcomes() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=8)

    survived = state.model_copy(update={"current_week": state.term_weeks + 1})
    failed = state.model_copy(update={"game_over_reason": "Stress hit the breaking point."})

    survived_summary = calculate_final_score(survived, bundle.scoring)
    failed_summary = calculate_final_score(failed, bundle.scoring)

    assert survived_summary.survived_term is True
    assert survived_summary.outcome == "survived"
    assert survived_summary.breakdown["survival_bonus"] == bundle.scoring.survival_bonus
    assert failed_summary.survived_term is False
    assert failed_summary.outcome == "failed"
    assert failed_summary.breakdown["survival_bonus"] == 0.0
