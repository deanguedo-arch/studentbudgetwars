from budgetwars.budget import apply_interest_and_fees, apply_weekly_expenses, apply_weekly_income
from budgetwars.events import resolve_event_choice
from budgetwars.game import check_game_over, start_new_game
from budgetwars.loaders import load_all_content
from budgetwars.scoring import calculate_final_score


def test_weekly_expense_application_uses_liquid_funds_then_debt() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=1)
    state = state.model_copy(
        update={
            "player": state.player.model_copy(update={"cash": 10, "savings": 5, "debt": 100}),
            "missed_essential_weeks": 0,
        }
    )

    updated = apply_weekly_expenses(state, bundle.expenses, expense_multiplier=1.0)

    assert updated.player.cash == 0
    assert updated.player.savings == 0
    assert updated.player.debt > 100
    assert updated.missed_essential_weeks == 1


def test_income_application_adds_cash_and_adjusts_stress_energy() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=2)
    job = next(job for job in bundle.jobs if job.id == state.player.job_id)

    updated = apply_weekly_income(state, job, income_multiplier=1.0, stress_multiplier=1.0)

    assert updated.player.cash > state.player.cash
    assert updated.player.energy < state.player.energy
    assert updated.player.stress >= state.player.stress


def test_event_application_uses_selected_choice() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=3)
    event = next(event for event in bundle.events if event.id == "textbook_shock")

    updated = resolve_event_choice(state, event, "put_on_credit")

    assert updated.player.debt == state.player.debt + 55
    assert updated.player.stress > state.player.stress


def test_game_over_checks_trigger_for_failure_conditions() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=4)

    stress_loss = state.model_copy(
        update={"player": state.player.model_copy(update={"stress": state.max_stress}), "game_over_reason": None}
    )
    energy_loss = state.model_copy(update={"consecutive_low_energy_weeks": state.low_energy_week_limit})
    debt_loss = state.model_copy(update={"player": state.player.model_copy(update={"debt": state.debt_game_over_threshold})})

    assert check_game_over(stress_loss) is True
    assert check_game_over(energy_loss) is True
    assert check_game_over(debt_loss) is True


def test_scoring_output_contains_breakdown_and_final_score() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=5)
    finished = state.model_copy(update={"current_week": state.term_weeks + 1})

    summary = calculate_final_score(finished, bundle.scoring)

    assert "cash" in summary.breakdown
    assert "survival_bonus" in summary.breakdown
    assert isinstance(summary.final_score, float)
    assert summary.survived_term is True


def test_interest_and_fees_increase_debt() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=6)
    state = state.model_copy(update={"player": state.player.model_copy(update={"debt": 200})})

    updated = apply_interest_and_fees(state, interest_rate=0.1, overdraft_fee=20)

    assert updated.player.debt > state.player.debt
