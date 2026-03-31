from budgetwars.budget import apply_optional_weekly_expenses, apply_weekly_income
from budgetwars.game import advance_week, check_game_over, start_new_game
from budgetwars.jobs import get_job, switch_job
from budgetwars.loaders import load_all_content


def test_optional_expense_pay_vs_skip_changes_state() -> None:
    bundle = load_all_content()
    expense = next(item for item in bundle.expenses if item.id == "transit_top_up")
    _, state = start_new_game(bundle=bundle, preset_id="default_student", seed=11)
    state = state.model_copy(update={"player": state.player.model_copy(update={"cash": 100, "stress": 20, "energy": 60})})

    paid = apply_optional_weekly_expenses(state, [expense], decisions={expense.id: True})
    skipped = apply_optional_weekly_expenses(state, [expense], decisions={expense.id: False})

    assert paid.player.cash == 88
    assert paid.player.stress == 19
    assert paid.player.energy == 62
    assert skipped.player.cash == 100
    assert skipped.player.stress == 22
    assert skipped.player.energy == 56


def test_jobs_have_distinct_weekly_outcomes() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, preset_id="default_student", seed=12)
    state = state.model_copy(update={"player": state.player.model_copy(update={"cash": 0, "stress": 20, "energy": 80})})

    library = get_job(bundle.jobs, "library_assistant")
    tutoring = get_job(bundle.jobs, "tutoring")
    delivery = get_job(bundle.jobs, "food_delivery")
    assert library is not None
    assert tutoring is not None
    assert delivery is not None

    library_week = apply_weekly_income(state, library)
    tutoring_week = apply_weekly_income(state, tutoring)
    delivery_week = apply_weekly_income(state, delivery)

    assert delivery_week.player.cash > library_week.player.cash > tutoring_week.player.cash
    assert delivery_week.player.energy < library_week.player.energy < tutoring_week.player.energy
    assert delivery_week.player.stress > library_week.player.stress >= tutoring_week.player.stress


def test_switching_to_high_strain_job_changes_week_dynamics() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, preset_id="default_student", seed=13)
    state = state.model_copy(update={"player": state.player.model_copy(update={"cash": 0, "stress": 20, "energy": 80})})

    library = get_job(bundle.jobs, "library_assistant")
    assert library is not None
    baseline = apply_weekly_income(state, library)

    switched = switch_job(
        state,
        bundle.jobs,
        "food_delivery",
        stress_penalty=bundle.config.job_switch_stress_penalty,
        sync_location_to_job=True,
    )
    switched_job = get_job(bundle.jobs, switched.player.job_id)
    assert switched_job is not None
    switched_week = apply_weekly_income(switched, switched_job)

    assert switched.player.job_id == "food_delivery"
    assert switched.player.location_id == "town_center"
    assert switched_week.player.cash > baseline.player.cash
    assert switched_week.player.energy < baseline.player.energy
    assert switched_week.player.stress > baseline.player.stress


def test_location_modifiers_affect_weekly_resolution() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, preset_id="default_student", seed=14)
    state = state.model_copy(
        update={
            "player": state.player.model_copy(
                update={"location_id": "town_center", "cash": 100, "stress": 30, "energy": 50}
            )
        }
    )
    quiet_bundle = bundle.model_copy(
        update={
            "expenses": [],
            "config": bundle.config.model_copy(
                update={"weekly_event_chance": 0.0, "debt_interest_rate": 0.0, "overdraft_fee": 0}
            ),
        }
    )

    updated = advance_week(
        state,
        quiet_bundle,
        action="rest",
        optional_expense_resolver=lambda _: True,
        choice_resolver=lambda _: None,
    )

    assert updated.player.cash == 95
    assert updated.player.stress == 22
    assert updated.player.energy == 68


def test_presets_start_with_distinct_profiles() -> None:
    bundle = load_all_content()
    _, default_state = start_new_game(bundle=bundle, preset_id="default_student", seed=15)
    _, commuter_state = start_new_game(bundle=bundle, preset_id="commuter_student", seed=15)
    _, stretched_state = start_new_game(bundle=bundle, preset_id="financially_stretched_student", seed=15)

    assert commuter_state.player.cash > default_state.player.cash > stretched_state.player.cash
    assert stretched_state.player.debt > default_state.player.debt > commuter_state.player.debt
    assert commuter_state.player.location_id != default_state.player.location_id
    assert stretched_state.player.job_id != default_state.player.job_id


def test_rebalanced_flow_keeps_game_over_logic_intact() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, preset_id="default_student", seed=16)
    state = state.model_copy(
        update={
            "player": state.player.model_copy(
                update={"stress": 99, "location_id": "town_center", "job_id": "library_assistant"}
            )
        }
    )
    pressure_bundle = bundle.model_copy(
        update={
            "expenses": [],
            "config": bundle.config.model_copy(
                update={"weekly_event_chance": 0.0, "debt_interest_rate": 0.0, "overdraft_fee": 0}
            ),
        }
    )

    updated = advance_week(
        state,
        pressure_bundle,
        action="work",
        optional_expense_resolver=lambda _: True,
        choice_resolver=lambda _: None,
    )

    assert check_game_over(updated) is True
    assert updated.game_over_reason == "Stress hit the breaking point."
