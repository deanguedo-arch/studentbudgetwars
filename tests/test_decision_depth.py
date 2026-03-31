from budgetwars.budget import apply_mandatory_weekly_expenses, apply_optional_weekly_expenses
from budgetwars.game import advance_week, check_game_over, start_new_game
from budgetwars.jobs import switch_job
from budgetwars.loaders import load_all_content
from budgetwars.locations import apply_location_effects
from budgetwars.models import ExpenseDefinition, GameState, JobDefinition, LocationDefinition, PlayerState


def _make_state(
    *,
    cash: int = 100,
    savings: int = 50,
    debt: int = 100,
    stress: int = 20,
    energy: int = 70,
) -> GameState:
    return GameState(
        game_title="Student Budget Wars",
        difficulty_id="normal",
        current_week=1,
        term_weeks=12,
        max_stress=100,
        max_energy=100,
        low_energy_threshold=15,
        low_energy_week_limit=2,
        debt_game_over_threshold=600,
        max_missed_essential_weeks=3,
        seed=42,
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


def test_location_stress_modifier_applies() -> None:
    state = _make_state(stress=30)
    location = LocationDefinition(
        id="focus_room",
        name="Focus Room",
        description="Quiet room",
        modifiers={"stress": -5},
    )

    updated = apply_location_effects(state, location)

    assert updated.player.stress == 25


def test_location_cash_modifier_applies() -> None:
    state = _make_state(cash=80)
    location = LocationDefinition(
        id="town_center",
        name="Town Center",
        description="Busy area",
        modifiers={"cash": -4},
    )

    updated = apply_location_effects(state, location)

    assert updated.player.cash == 76


def test_location_energy_modifier_clamps_to_max() -> None:
    state = _make_state(energy=98)
    location = LocationDefinition(
        id="recovery_zone",
        name="Recovery Zone",
        description="Low pressure area",
        modifiers={"energy": 10},
    )

    updated = apply_location_effects(state, location)

    assert updated.player.energy == 100


def test_job_switch_updates_job_location_and_penalty() -> None:
    state = _make_state(stress=22)
    jobs = [
        JobDefinition(
            id="library_assistant",
            name="Library Assistant",
            hourly_pay=15,
            hours_per_week=10,
            energy_cost=12,
            stress_delta=2,
            location_id="campus_library",
            description="Current job",
        ),
        JobDefinition(
            id="barista",
            name="Barista",
            hourly_pay=17,
            hours_per_week=10,
            energy_cost=15,
            stress_delta=4,
            location_id="town_center",
            description="New job",
        ),
    ]

    updated = switch_job(state, jobs, "barista", stress_penalty=4, sync_location_to_job=True)

    assert updated.player.job_id == "barista"
    assert updated.player.location_id == "town_center"
    assert updated.player.stress == 26


def test_invalid_job_switch_is_safe() -> None:
    state = _make_state(stress=22)
    jobs = [
        JobDefinition(
            id="library_assistant",
            name="Library Assistant",
            hourly_pay=15,
            hours_per_week=10,
            energy_cost=12,
            stress_delta=2,
            location_id="campus_library",
            description="Current job",
        )
    ]

    updated = switch_job(state, jobs, "missing_job", stress_penalty=4, sync_location_to_job=True)

    assert updated.player == state.player
    assert "Invalid job selection" in updated.message_log[-1]


def test_optional_expense_paid_applies_cost_and_pay_effect() -> None:
    state = _make_state(cash=50, stress=20, energy=70)
    expenses = [
        ExpenseDefinition(
            id="fun_budget",
            name="Fun Budget",
            amount=10,
            cadence="weekly",
            mandatory=False,
            description="Optional",
            pay_effects={"stress": -2},
            skip_effects={"stress": 3},
        )
    ]

    updated = apply_optional_weekly_expenses(state, expenses, decisions={"fun_budget": True})

    assert updated.player.cash == 40
    assert updated.player.stress == 18


def test_optional_expense_skipped_applies_skip_penalty() -> None:
    state = _make_state(cash=50, stress=20, energy=70)
    expenses = [
        ExpenseDefinition(
            id="fun_budget",
            name="Fun Budget",
            amount=10,
            cadence="weekly",
            mandatory=False,
            description="Optional",
            pay_effects={"stress": -2},
            skip_effects={"stress": 3, "energy": -2},
        )
    ]

    updated = apply_optional_weekly_expenses(state, expenses, decisions={"fun_budget": False})

    assert updated.player.cash == 50
    assert updated.player.stress == 23
    assert updated.player.energy == 68


def test_mandatory_expenses_still_auto_apply() -> None:
    state = _make_state(cash=60, savings=20, debt=100)
    expenses = [
        ExpenseDefinition(
            id="rent",
            name="Rent",
            amount=50,
            cadence="weekly",
            mandatory=True,
            description="Mandatory",
        ),
        ExpenseDefinition(
            id="fun_budget",
            name="Fun Budget",
            amount=10,
            cadence="weekly",
            mandatory=False,
            description="Optional",
            skip_effects={"stress": 2},
        ),
    ]

    updated = apply_mandatory_weekly_expenses(state, expenses)

    assert updated.player.cash == 10
    assert updated.player.savings == 20
    assert updated.player.debt == 100


def test_uncovered_mandatory_expense_rolls_into_debt() -> None:
    state = _make_state(cash=20, savings=10, debt=100)
    expenses = [
        ExpenseDefinition(
            id="rent",
            name="Rent",
            amount=80,
            cadence="weekly",
            mandatory=True,
            description="Mandatory",
        )
    ]

    updated = apply_mandatory_weekly_expenses(state, expenses)

    assert updated.player.cash == 0
    assert updated.player.savings == 0
    assert updated.player.debt == 150
    assert updated.missed_essential_weeks == 1


def test_weekly_flow_preserves_game_over_logic_with_new_steps() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, seed=101)
    state = state.model_copy(update={"player": state.player.model_copy(update={"stress": 20})})

    modified_locations = [
        location.model_copy(update={"modifiers": {"stress": 120}})
        if location.id == state.player.location_id
        else location
        for location in bundle.locations
    ]
    modified_bundle = bundle.model_copy(
        update={
            "expenses": [],
            "locations": modified_locations,
            "config": bundle.config.model_copy(
                update={"weekly_event_chance": 0.0, "debt_interest_rate": 0.0, "overdraft_fee": 0}
            ),
        }
    )

    updated = advance_week(
        state,
        modified_bundle,
        action="rest",
        optional_expense_resolver=lambda _: True,
        choice_resolver=lambda _: None,
    )

    assert check_game_over(updated) is True
    assert updated.game_over_reason == "Stress hit the breaking point."
