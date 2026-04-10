from __future__ import annotations

from budgetwars.engine.events import eligible_events, resolve_event
from budgetwars.models import PendingEvent
from budgetwars.models.content import EventChoice, EventDefinition, ModifierTemplate


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


def test_event_choice_can_apply_modifier(bundle, controller_factory) -> None:
    controller = controller_factory()
    event = EventDefinition(
        id="refinance_test",
        name="Refinance Test",
        description="A test event that grants a modifier after a choice.",
        weight=1,
        choices=[
            EventChoice(
                id="take_it",
                label="Take it",
                description="Lock in the better terms.",
                stat_effects={"debt": -100},
                modifier=ModifierTemplate(
                    id="better_terms",
                    label="Better Terms",
                    duration_months=3,
                    living_cost_delta=-25,
                ),
            )
        ],
    )

    resolve_event(bundle, controller.state, event)
    controller.resolve_event_choice("take_it")

    assert any(modifier.id == "better_terms" for modifier in controller.state.active_modifiers)


def test_refinance_window_only_grants_relief_when_taken(bundle, controller_factory) -> None:
    event = next(item for item in bundle.events if item.id == "refinance_window")

    wait_controller = controller_factory()
    wait_controller.state.player.credit_score = 720
    wait_controller.state.player.debt = 5000
    resolve_event(bundle, wait_controller.state, event)
    wait_controller.resolve_event_choice("wait_for_better_rate")

    take_controller = controller_factory()
    take_controller.state.player.credit_score = 720
    take_controller.state.player.debt = 5000
    resolve_event(bundle, take_controller.state, event)
    take_controller.resolve_event_choice("refinance_now")

    assert not any(modifier.id == "refinance_relief" for modifier in wait_controller.state.active_modifiers)
    assert any(modifier.id == "refinance_relief" for modifier in take_controller.state.active_modifiers)


def test_promotion_window_is_a_real_choice_event(bundle) -> None:
    event = next(item for item in bundle.events if item.id == "promotion_window")

    assert event.choices
    assert len(event.choices) >= 2


def test_promotion_window_scope_choices_have_persistent_modifiers(bundle) -> None:
    event = next(item for item in bundle.events if item.id == "promotion_window")
    by_id = {choice.id: choice for choice in event.choices}

    assert by_id["push_for_scope"].modifier is not None
    assert by_id["bank_consistency"].modifier is not None
    assert by_id["push_for_scope"].modifier.duration_months >= 8
    assert by_id["bank_consistency"].modifier.duration_months >= 8


def test_branch_promotion_offer_events_are_choice_events(bundle) -> None:
    retail_offer = next(item for item in bundle.events if item.id == "retail_leadership_offer")
    warehouse_offer = next(item for item in bundle.events if item.id == "dispatch_lead_offer")

    assert len(retail_offer.choices) >= 2
    assert len(warehouse_offer.choices) >= 2


def test_retail_promotion_choice_alters_future_event_pool(bundle, controller_factory) -> None:
    push = controller_factory(opening_path_id="full_time_work")
    push.change_career("retail_service")
    push.state.current_month = 24
    push.state.player.career.tier_index = 3
    push.state.player.career.branch_id = "retail_management_track"
    push.state.player.social_stability = 64
    push.state.player.transport.reliability_score = 70
    offer = next(item for item in bundle.events if item.id == "retail_leadership_offer")
    resolve_event(bundle, push.state, offer)
    push.resolve_event_choice("take_closing_command")
    push_ids = {event.id for event in eligible_events(bundle, push.state)}

    stabilize = controller_factory(opening_path_id="full_time_work")
    stabilize.change_career("retail_service")
    stabilize.state.current_month = 24
    stabilize.state.player.career.tier_index = 3
    stabilize.state.player.career.branch_id = "retail_management_track"
    stabilize.state.player.social_stability = 64
    stabilize.state.player.transport.reliability_score = 70
    resolve_event(bundle, stabilize.state, offer)
    stabilize.resolve_event_choice("stabilize_the_floor")
    stabilize_ids = {event.id for event in eligible_events(bundle, stabilize.state)}

    assert "management_overload_wave" in push_ids
    assert "floor_culture_retention_win" not in push_ids
    assert "floor_culture_retention_win" in stabilize_ids
    assert "management_overload_wave" not in stabilize_ids


def test_dispatch_promotion_choice_alters_future_event_pool(bundle, controller_factory) -> None:
    command = controller_factory(opening_path_id="full_time_work")
    command.state.current_month = 24
    command.state.player.career.tier_index = 3
    command.state.player.career.branch_id = "warehouse_dispatch_track"
    command.state.player.transport.reliability_score = 74
    command.state.player.social_stability = 60
    offer = next(item for item in bundle.events if item.id == "dispatch_lead_offer")
    resolve_event(bundle, command.state, offer)
    command.resolve_event_choice("own_the_board")
    command_ids = {event.id for event in eligible_events(bundle, command.state)}

    coordination = controller_factory(opening_path_id="full_time_work")
    coordination.state.current_month = 24
    coordination.state.player.career.tier_index = 3
    coordination.state.player.career.branch_id = "warehouse_dispatch_track"
    coordination.state.player.transport.reliability_score = 74
    coordination.state.player.social_stability = 60
    resolve_event(bundle, coordination.state, offer)
    coordination.resolve_event_choice("stay_coordination")
    coordination_ids = {event.id for event in eligible_events(bundle, coordination.state)}

    assert "dispatch_fire_drill" in command_ids
    assert "dispatch_process_upgrade" not in command_ids
    assert "dispatch_process_upgrade" in coordination_ids
    assert "dispatch_fire_drill" not in coordination_ids


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


def test_top_victory_requires_stability_not_just_money(controller_factory) -> None:
    controller = controller_factory()
    player = controller.state.player
    player.cash = 180_000
    player.savings = 35_000
    player.high_interest_savings = 10_000
    player.index_fund = 15_000
    player.aggressive_growth_fund = 8_000
    player.debt = 0
    player.credit_score = 560
    player.housing.housing_stability = 38
    player.social_stability = 34
    player.career.tier_index = len(controller.bundle.careers[0].tiers) - 1
    player.career.track_id = controller.bundle.careers[0].id
    player.emergency_liquidation_count = 2

    eligible_ids = {win_state.id for win_state in controller.available_win_states()}

    assert "life_position" not in eligible_ids
    assert "financial_anchor" not in eligible_ids


def test_branch_specific_victory_requires_matching_branch(controller_factory) -> None:
    dispatch = controller_factory(opening_path_id="full_time_work")
    player = dispatch.state.player
    player.cash = 95_000
    player.savings = 22_000
    player.high_interest_savings = 12_000
    player.index_fund = 18_000
    player.aggressive_growth_fund = 6_000
    player.debt = 2_000
    player.credit_score = 735
    player.housing.housing_stability = 78
    player.social_stability = 66
    player.career.track_id = "warehouse_logistics"
    player.career.branch_id = "warehouse_dispatch_track"
    player.career.tier_index = 4

    equipment = controller_factory(opening_path_id="full_time_work")
    other = equipment.state.player
    other.cash = player.cash
    other.savings = player.savings
    other.high_interest_savings = player.high_interest_savings
    other.index_fund = player.index_fund
    other.aggressive_growth_fund = player.aggressive_growth_fund
    other.debt = player.debt
    other.credit_score = player.credit_score
    other.housing.housing_stability = player.housing.housing_stability
    other.social_stability = player.social_stability
    other.career.track_id = "warehouse_logistics"
    other.career.branch_id = "warehouse_equipment_track"
    other.career.tier_index = 4

    dispatch_ids = {win_state.id for win_state in dispatch.available_win_states()}
    equipment_ids = {win_state.id for win_state in equipment.available_win_states()}

    assert "dispatch_anchor" in dispatch_ids
    assert "dispatch_anchor" not in equipment_ids


def test_client_book_victory_requires_clienteling_branch(controller_factory) -> None:
    clienteling = controller_factory(opening_path_id="full_time_work")
    clienteling.change_career("retail_service")
    player = clienteling.state.player
    player.cash = 92_000
    player.savings = 24_000
    player.high_interest_savings = 10_000
    player.index_fund = 14_000
    player.aggressive_growth_fund = 5_000
    player.debt = 1_500
    player.credit_score = 730
    player.housing.housing_stability = 75
    player.social_stability = 72
    player.career.branch_id = "retail_clienteling_track"
    player.career.tier_index = 4

    management = controller_factory(opening_path_id="full_time_work")
    management.change_career("retail_service")
    other = management.state.player
    other.cash = player.cash
    other.savings = player.savings
    other.high_interest_savings = player.high_interest_savings
    other.index_fund = player.index_fund
    other.aggressive_growth_fund = player.aggressive_growth_fund
    other.debt = player.debt
    other.credit_score = player.credit_score
    other.housing.housing_stability = player.housing.housing_stability
    other.social_stability = player.social_stability
    other.career.branch_id = "retail_management_track"
    other.career.tier_index = 4

    clienteling_ids = {win_state.id for win_state in clienteling.available_win_states()}
    management_ids = {win_state.id for win_state in management.available_win_states()}

    assert "client_book_position" in clienteling_ids
    assert "client_book_position" not in management_ids


def test_victory_claims_block_when_major_fallout_is_still_pending(controller_factory) -> None:
    controller = controller_factory(opening_path_id="full_time_work")
    player = controller.state.player
    player.cash = 120_000
    player.savings = 24_000
    player.high_interest_savings = 10_000
    player.index_fund = 14_000
    player.aggressive_growth_fund = 5_000
    player.debt = 2_000
    player.credit_score = 742
    player.housing.housing_stability = 76
    player.social_stability = 66
    player.monthly_surplus = 500
    player.stress = 40
    player.energy = 70
    player.career.tier_index = 4
    player.career.track_id = "warehouse_logistics"
    player.career.branch_id = "warehouse_dispatch_track"

    controller.state.pending_events.append(
        PendingEvent(
            event_id="credit_limit_review",
            months_remaining=1,
            source_event_id="collections_warning",
        )
    )
    controller.state.pending_user_choice_event_id = "collections_warning"

    eligible_ids = {win_state.id for win_state in controller.available_win_states()}

    assert "dispatch_anchor" not in eligible_ids
    assert "life_position" not in eligible_ids
