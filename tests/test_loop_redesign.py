from budgetwars.game import advance_week, build_week_outlook, compress_week_messages, start_new_game
from budgetwars.loaders import load_all_content
from budgetwars.locations import move_location


def test_move_location_updates_state_with_penalty() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, preset_id="default_student", seed=210)
    initial_stress = state.player.stress

    moved = move_location(
        state,
        bundle.locations,
        "grocery_store",
        stress_penalty=bundle.config.location_move_stress_penalty,
    )

    assert moved.player.location_id == "grocery_store"
    assert moved.player.stress == initial_stress + bundle.config.location_move_stress_penalty
    assert any("Moved to" in message for message in moved.message_log)


def test_invalid_location_move_is_safe() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, preset_id="default_student", seed=211)

    moved = move_location(state, bundle.locations, "missing_location", stress_penalty=1)

    assert moved.player == state.player
    assert "Invalid location selection" in moved.message_log[-1]


def test_offsite_work_penalty_applies_when_location_mismatches_job() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, preset_id="default_student", seed=212)
    state = state.model_copy(
        update={"player": state.player.model_copy(update={"location_id": "campus_dorm", "stress": 20, "energy": 70})}
    )
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

    updated = advance_week(
        state,
        quiet_bundle,
        action="work",
        optional_expense_resolver=lambda _: True,
        choice_resolver=lambda _: None,
    )

    assert updated.player.energy == 58
    assert updated.player.stress == 23
    assert any("Offsite work strain" in message for message in updated.message_log)


def test_work_at_job_location_avoids_offsite_penalty() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, preset_id="default_student", seed=213)
    state = state.model_copy(
        update={"player": state.player.model_copy(update={"location_id": "campus_library", "stress": 20, "energy": 70})}
    )
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

    updated = advance_week(
        state,
        quiet_bundle,
        action="work",
        optional_expense_resolver=lambda _: True,
        choice_resolver=lambda _: None,
    )

    assert updated.player.energy == 62
    assert updated.player.stress == 21
    assert all("Offsite work strain" not in message for message in updated.message_log)


def test_week_message_compression_reduces_admin_noise() -> None:
    messages = [
        "older message",
        "Resolving week 4.",
        "Paid Dorm Fee (125) using cash/savings.",
        "Paid Groceries (32) using cash/savings and debt.",
        "Optional expense paid (Transit Top-Up): stress -1.",
        "Optional expense skipped (Laundry Upkeep): stress +3.",
        "Temporary effect active (Commute Drag): energy -2.",
        "Event effects (Class Project Week): stress +2.",
        "Event: Class Project Week -> Push through.",
        "Debt interest added 10.",
    ]

    compact = compress_week_messages(messages, 1)

    assert "older message" in compact[0]
    assert any("Weekly essentials:" in message for message in compact)
    assert any("Optional choices:" in message for message in compact)
    assert any("Carryover effects applied this week:" in message for message in compact)
    assert any("Event: Class Project Week" in message for message in compact)
    assert all(not message.startswith("Paid ") for message in compact)


def test_week_outlook_surfaces_pressure_signals() -> None:
    bundle = load_all_content()
    _, state = start_new_game(bundle=bundle, preset_id="default_student", seed=214)
    state = state.model_copy(
        update={
            "player": state.player.model_copy(
                update={
                    "debt": 500,
                    "energy": 17,
                    "stress": 89,
                    "location_id": "campus_dorm",
                    "job_id": "food_delivery",
                }
            )
        }
    )

    lines = build_week_outlook(state, bundle)

    assert 1 <= len(lines) <= 6
    assert any("Location pressure" in line for line in lines)
    assert any("Job reality" in line for line in lines)
    assert any("Debt pressure" in line for line in lines)
    assert any("Energy is low" in line or "Stress is near" in line for line in lines)
