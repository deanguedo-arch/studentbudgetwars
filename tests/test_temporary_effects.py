from budgetwars.budget import (
    add_temporary_effects,
    apply_optional_weekly_expenses,
    apply_start_of_week_temporary_effects,
    decrement_temporary_effects,
)
from budgetwars.events import resolve_event_choice
from budgetwars.game import advance_week, check_game_over, start_new_game
from budgetwars.loaders import load_all_content
from budgetwars.models import (
    ActiveTemporaryEffect,
    EventChoiceDefinition,
    EventDefinition,
    ExpenseDefinition,
    GameState,
    PlayerState,
    TemporaryEffectDefinition,
)


def _make_state(
    *,
    stress: int = 20,
    energy: int = 60,
    cash: int = 100,
    temporary_effects: list[ActiveTemporaryEffect] | None = None,
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
            savings=40,
            debt=120,
            stress=stress,
            energy=energy,
            location_id="campus_dorm",
            job_id="library_assistant",
        ),
        temporary_effects=temporary_effects or [],
    )


def test_temporary_effect_applies_and_expires_after_duration() -> None:
    state = _make_state(
        temporary_effects=[
            ActiveTemporaryEffect(
                id="rough_week",
                label="Rough Week",
                remaining_weeks=1,
                effects={"stress": 4, "energy": -3},
            )
        ]
    )

    applied = apply_start_of_week_temporary_effects(state)
    assert applied.player.stress == 24
    assert applied.player.energy == 57

    expired = decrement_temporary_effects(applied, active_effects_at_week_start=1)
    assert expired.temporary_effects == []
    assert any("Temporary effect expired: Rough Week." in message for message in expired.message_log)


def test_multiple_temporary_effects_apply_and_clamp_in_same_week() -> None:
    state = _make_state(
        stress=95,
        energy=4,
        temporary_effects=[
            ActiveTemporaryEffect(
                id="stack_a",
                label="Stack A",
                remaining_weeks=1,
                effects={"stress": 4, "energy": -3},
            ),
            ActiveTemporaryEffect(
                id="stack_b",
                label="Stack B",
                remaining_weeks=1,
                effects={"stress": 6, "energy": -5},
            ),
        ],
    )

    updated = apply_start_of_week_temporary_effects(state)

    assert updated.player.stress == 100
    assert updated.player.energy == 0


def test_existing_effects_apply_before_new_effects_and_new_effects_do_not_expire_immediately() -> None:
    state = _make_state(
        stress=20,
        temporary_effects=[
            ActiveTemporaryEffect(
                id="old_effect",
                label="Old Effect",
                remaining_weeks=1,
                effects={"stress": 3},
            )
        ],
    )

    start_applied = apply_start_of_week_temporary_effects(state)
    with_new_effect = add_temporary_effects(
        start_applied,
        [
            TemporaryEffectDefinition(
                id="new_effect",
                label="New Effect",
                duration_weeks=1,
                effects={"stress": 5},
            )
        ],
        "Test source",
    )
    decremented = decrement_temporary_effects(with_new_effect, active_effects_at_week_start=1)

    assert start_applied.player.stress == 23
    assert with_new_effect.player.stress == 23
    assert len(decremented.temporary_effects) == 1
    assert decremented.temporary_effects[0].id == "new_effect"
    assert decremented.temporary_effects[0].remaining_weeks == 1


def test_multiple_temporary_effects_expire_correctly() -> None:
    state = _make_state(
        temporary_effects=[
            ActiveTemporaryEffect(
                id="expire_a",
                label="Expire A",
                remaining_weeks=1,
                effects={"stress": 1},
            ),
            ActiveTemporaryEffect(
                id="expire_b",
                label="Expire B",
                remaining_weeks=1,
                effects={"energy": -1},
            ),
        ]
    )

    updated = decrement_temporary_effects(state, active_effects_at_week_start=2)

    assert updated.temporary_effects == []
    assert sum(1 for message in updated.message_log if "Temporary effect expired:" in message) == 2


def test_optional_expense_paid_adds_temporary_effect() -> None:
    state = _make_state(cash=50, stress=30, energy=55)
    expense = ExpenseDefinition(
        id="laundry_upkeep",
        name="Laundry Upkeep",
        amount=10,
        cadence="weekly",
        mandatory=False,
        description="Upkeep",
        pay_effects={"stress": -1},
        skip_effects={"stress": 2},
        pay_temporary_effects=[
            TemporaryEffectDefinition(
                id="organized_week",
                label="Organized Week",
                duration_weeks=1,
                effects={"stress": -1, "energy": 1},
            )
        ],
    )

    updated = apply_optional_weekly_expenses(state, [expense], decisions={"laundry_upkeep": True})

    assert updated.player.cash == 40
    assert updated.player.stress == 29
    assert len(updated.temporary_effects) == 1
    assert updated.temporary_effects[0].id == "organized_week"


def test_optional_expense_skipped_adds_penalty_temporary_effect() -> None:
    state = _make_state(cash=50, stress=30, energy=55)
    expense = ExpenseDefinition(
        id="transit_top_up",
        name="Transit Top-Up",
        amount=12,
        cadence="weekly",
        mandatory=False,
        description="Transit",
        pay_effects={"energy": 1},
        skip_effects={"stress": 2},
        skip_temporary_effects=[
            TemporaryEffectDefinition(
                id="commute_drag",
                label="Commute Drag",
                duration_weeks=1,
                effects={"energy": -2, "stress": 1},
            )
        ],
    )

    updated = apply_optional_weekly_expenses(state, [expense], decisions={"transit_top_up": False})

    assert updated.player.cash == 50
    assert updated.player.stress == 32
    assert len(updated.temporary_effects) == 1
    assert updated.temporary_effects[0].id == "commute_drag"


def test_event_choice_can_add_temporary_effects() -> None:
    state = _make_state(stress=20, energy=60)
    event = EventDefinition(
        id="class_project_week",
        name="Class Project Week",
        description="Project pressure",
        weight=1,
        effects={"stress": 2},
        temporary_effects=[
            TemporaryEffectDefinition(
                id="project_tail",
                label="Project Tail",
                duration_weeks=1,
                effects={"stress": 1},
            )
        ],
        choices=[
            EventChoiceDefinition(
                id="grind",
                label="Grind Through",
                description="Push hard",
                effects={"energy": -4},
                temporary_effects=[
                    TemporaryEffectDefinition(
                        id="burnout_tail",
                        label="Burnout Tail",
                        duration_weeks=1,
                        effects={"stress": 2, "energy": -2},
                    )
                ],
            )
        ],
    )

    updated = resolve_event_choice(state, event, "grind")

    assert updated.player.stress == 22
    assert updated.player.energy == 56
    assert {effect.id for effect in updated.temporary_effects} == {"project_tail", "burnout_tail"}


def test_work_week_adds_job_carryover_for_next_week_only() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, preset_id="default_student", seed=123)
    state = state.model_copy(update={"player": state.player.model_copy(update={"stress": 30, "energy": 80})})
    quiet_bundle = bundle.model_copy(
        update={
            "expenses": [],
            "events": [],
            "locations": [location.model_copy(update={"modifiers": {}}) for location in bundle.locations],
            "config": bundle.config.model_copy(
                update={"weekly_event_chance": 0.0, "debt_interest_rate": 0.0, "overdraft_fee": 0}
            ),
        }
    )

    week_one = advance_week(
        state,
        quiet_bundle,
        action="work",
        optional_expense_resolver=lambda _: True,
        choice_resolver=lambda _: None,
    )

    assert any(effect.id == "quiet_routine" for effect in week_one.temporary_effects)
    assert week_one.player.stress == 31

    week_two = advance_week(
        week_one,
        quiet_bundle,
        action="rest",
        optional_expense_resolver=lambda _: True,
        choice_resolver=lambda _: None,
    )

    assert week_two.player.stress == 20
    assert week_two.temporary_effects == []


def test_game_over_logic_still_triggers_with_active_temporary_effects() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, preset_id="default_student", seed=321)
    state = state.model_copy(
        update={
            "player": state.player.model_copy(update={"stress": 96, "energy": 80}),
            "temporary_effects": [
                ActiveTemporaryEffect(
                    id="panic_spike",
                    label="Panic Spike",
                    remaining_weeks=1,
                    effects={"stress": 6},
                ),
                ActiveTemporaryEffect(
                    id="drain_wave",
                    label="Drain Wave",
                    remaining_weeks=1,
                    effects={"energy": -12, "stress": 2},
                ),
            ],
        }
    )
    pressure_bundle = bundle.model_copy(
        update={
            "expenses": [],
            "events": [],
            "locations": [location.model_copy(update={"modifiers": {}}) for location in bundle.locations],
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
