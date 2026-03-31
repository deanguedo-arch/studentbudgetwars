from budgetwars.budget import apply_rest_action, apply_weekly_expenses, apply_weekly_income
from budgetwars.events import resolve_event_choice
from budgetwars.game import check_game_over
from budgetwars.models import (
    EventChoiceDefinition,
    EventDefinition,
    ExpenseDefinition,
    GameState,
    JobDefinition,
    PlayerState,
    ScoringDefinition,
)
from budgetwars.scoring import calculate_final_score


def _make_state(
    *,
    cash: int = 100,
    savings: int = 50,
    debt: int = 100,
    stress: int = 20,
    energy: int = 70,
    current_week: int = 1,
    term_weeks: int = 12,
    consecutive_low_energy_weeks: int = 0,
    debt_game_over_threshold: int = 600,
    low_energy_week_limit: int = 2,
    game_over_reason: str | None = None,
) -> GameState:
    return GameState(
        game_title="Student Budget Wars",
        difficulty_id="normal",
        current_week=current_week,
        term_weeks=term_weeks,
        max_stress=100,
        max_energy=100,
        low_energy_threshold=15,
        low_energy_week_limit=low_energy_week_limit,
        debt_game_over_threshold=debt_game_over_threshold,
        max_missed_essential_weeks=3,
        seed=42,
        consecutive_low_energy_weeks=consecutive_low_energy_weeks,
        game_over_reason=game_over_reason,
        player=PlayerState(
            name="Tester",
            cash=cash,
            savings=savings,
            debt=debt,
            stress=stress,
            energy=energy,
            location_id="campus_dorm",
            job_id="library_assistant",
        ),
    )


def test_apply_weekly_expenses_uses_cash_then_savings() -> None:
    state = _make_state(cash=100, savings=50, debt=100)
    expenses = [
        ExpenseDefinition(
            id="rent",
            name="Rent",
            amount=120,
            cadence="weekly",
            mandatory=True,
            description="Test expense",
        )
    ]

    updated = apply_weekly_expenses(state, expenses)

    assert updated.player.cash == 0
    assert updated.player.savings == 30
    assert updated.player.debt == 100
    assert updated.missed_essential_weeks == 0


def test_uncovered_mandatory_expenses_increase_debt() -> None:
    state = _make_state(cash=40, savings=10, debt=100)
    expenses = [
        ExpenseDefinition(
            id="rent",
            name="Rent",
            amount=80,
            cadence="weekly",
            mandatory=True,
            description="Test expense",
        )
    ]

    updated = apply_weekly_expenses(state, expenses)

    assert updated.player.cash == 0
    assert updated.player.savings == 0
    assert updated.player.debt == 130
    assert updated.missed_essential_weeks == 1


def test_apply_weekly_income_updates_cash_stress_energy() -> None:
    state = _make_state(cash=10, stress=5, energy=50)
    job = JobDefinition(
        id="test_job",
        name="Test Job",
        hourly_pay=20,
        hours_per_week=5,
        energy_cost=6,
        stress_delta=3,
        location_id="campus_library",
        description="Test job",
    )

    updated = apply_weekly_income(state, job, income_multiplier=1.0, stress_multiplier=1.0)

    assert updated.player.cash == 110
    assert updated.player.stress == 8
    assert updated.player.energy == 44


def test_rest_action_changes_stress_and_energy() -> None:
    state = _make_state(stress=24, energy=78)

    updated = apply_rest_action(state)

    assert updated.player.stress == 14
    assert updated.player.energy == 96


def test_resolve_event_choice_applies_base_plus_choice_effects() -> None:
    state = _make_state(cash=100, debt=200, stress=20, energy=60)
    event = EventDefinition(
        id="event_1",
        name="Test Event",
        description="Test event",
        weight=1,
        effects={"stress": 2, "cash": -10},
        choices=[
            EventChoiceDefinition(
                id="choice_1",
                label="Take option",
                description="Option description",
                effects={"debt": 15, "stress": 3},
            )
        ],
    )

    updated = resolve_event_choice(state, event, "choice_1")

    assert updated.player.cash == 90
    assert updated.player.debt == 215
    assert updated.player.stress == 25
    assert updated.player.energy == 60


def test_low_energy_streak_triggers_game_over() -> None:
    state = _make_state(consecutive_low_energy_weeks=2, low_energy_week_limit=2)
    assert check_game_over(state) is True


def test_debt_threshold_triggers_game_over() -> None:
    state = _make_state(debt=500, debt_game_over_threshold=500)
    assert check_game_over(state) is True


def test_calculate_final_score_survived_vs_failed() -> None:
    scoring = ScoringDefinition(
        cash_weight=1.0,
        savings_weight=1.5,
        debt_weight=-1.25,
        stress_weight=-0.75,
        energy_weight=0.5,
        survival_bonus=100.0,
        failure_floor=-100.0,
    )
    survived_state = _make_state(current_week=13, term_weeks=12, game_over_reason=None)
    failed_state = _make_state(current_week=5, term_weeks=12, game_over_reason="Debt spiraled out of control.")

    survived_summary = calculate_final_score(survived_state, scoring)
    failed_summary = calculate_final_score(failed_state, scoring)

    assert survived_summary.survived_term is True
    assert survived_summary.outcome == "survived"
    assert survived_summary.breakdown["survival_bonus"] == 100.0
    assert failed_summary.survived_term is False
    assert failed_summary.outcome == "failed"
    assert failed_summary.breakdown["survival_bonus"] == 0.0
