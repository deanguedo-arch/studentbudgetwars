from __future__ import annotations

from budgetwars.engine.events import resolve_event
from budgetwars.models.content import EventChoice, EventDefinition


def test_bundle_loads_win_states_and_choice_events(bundle) -> None:
    assert len(bundle.win_states) >= 3
    assert any(event.choices for event in bundle.events)


def test_choice_event_sets_pending_choice_without_applying_effects(bundle, controller_factory) -> None:
    controller = controller_factory()
    event_data = bundle.events[0].model_dump()
    event_data["id"] = "choice_test"
    event_data["name"] = "Choice Test"
    event_data["description"] = "A choice-based event for testing."
    event_data["choices"] = [
        {
            "id": "pay_up",
            "label": "Pay up",
            "description": "Take the safe route.",
            "stat_effects": {"cash": -100, "stress": -1},
        },
        {
            "id": "walk_away",
            "label": "Walk away",
            "description": "Take the risky route.",
            "stat_effects": {"stress": 3, "social_stability": -2},
        },
    ]
    event = EventDefinition.model_validate(event_data)

    starting_cash = controller.state.player.cash
    starting_stress = controller.state.player.stress

    resolve_event(bundle, controller.state, event)

    assert controller.state.pending_user_choice_event_id == "choice_test"
    assert controller.state.player.cash == starting_cash
    assert controller.state.player.stress == starting_stress


def test_resolve_event_choice_applies_effects_and_clears_pending(bundle, controller_factory) -> None:
    controller = controller_factory()
    event_data = bundle.events[0].model_dump()
    event_data["id"] = "choice_test"
    event_data["name"] = "Choice Test"
    event_data["description"] = "A choice-based event for testing."
    event_data["choices"] = [
        {
            "id": "pay_up",
            "label": "Pay up",
            "description": "Take the safe route.",
            "stat_effects": {"cash": -100, "stress": -1},
        },
        {
            "id": "walk_away",
            "label": "Walk away",
            "description": "Take the risky route.",
            "stat_effects": {"stress": 3, "social_stability": -2},
        },
    ]
    event = EventDefinition.model_validate(event_data)

    resolve_event(bundle, controller.state, event)
    controller.resolve_event_choice("pay_up")

    assert controller.state.pending_user_choice_event_id is None
    assert controller.state.player.cash == controller_factory().state.player.cash - 100
    assert controller.state.player.stress == controller_factory().state.player.stress - 1


def test_event_choice_can_adjust_credit_score(bundle, controller_factory) -> None:
    controller = controller_factory()
    event = EventDefinition(
        id="credit_review",
        name="Credit Review",
        description="A test event that touches credit.",
        weight=1,
        choices=[
            EventChoice(
                id="tighten_up",
                label="Tighten up",
                description="Protect your credit.",
                stat_effects={"credit_score": 12},
            )
        ],
    )

    starting_credit = controller.state.player.credit_score

    resolve_event(bundle, controller.state, event)
    controller.resolve_event_choice("tighten_up")

    assert controller.state.player.credit_score == starting_credit + 12


def test_declare_victory_finishes_run_with_multiplier(controller_factory) -> None:
    controller = controller_factory()
    player = controller.state.player
    player.cash = 120_000
    player.savings = 20_000
    player.debt = 0
    player.career.tier_index = len(controller.bundle.careers[0].tiers) - 1
    player.career.track_id = controller.bundle.careers[0].id

    eligible = controller.available_win_states()

    assert eligible

    win_state = eligible[0]
    controller.declare_victory(win_state.id)

    assert controller.is_finished()
    assert controller.state.victory_state_id == win_state.id
    summary = controller.final_score_summary()
    assert summary.final_score > 0
    assert summary.ending_label == win_state.ending_label
