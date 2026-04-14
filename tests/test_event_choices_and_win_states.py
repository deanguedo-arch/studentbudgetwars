from __future__ import annotations

import pytest

from budgetwars.engine.events import eligible_events, resolve_event
from budgetwars.models import PendingEvent
from budgetwars.models.content import EventChoice, EventDefinition, ModifierTemplate


def _seed_branch_offer_state(
    controller,
    *,
    track_id: str,
    branch_id: str,
    month: int = 24,
    social_stability: int = 66,
    transport_reliability: int = 76,
    stress: int = 50,
    energy: int = 62,
    credit_score: int = 720,
    debt: int = 4200,
) -> None:
    state = controller.state
    state.current_month = month
    state.player.career.track_id = track_id
    state.player.career.tier_index = 3
    state.player.career.branch_id = branch_id
    state.player.social_stability = social_stability
    state.player.transport.reliability_score = transport_reliability
    state.player.stress = stress
    state.player.energy = energy
    state.player.credit_score = credit_score
    state.player.debt = debt


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
    assert by_id["push_for_scope"].persistent_tag == "scope_push_lane"
    assert by_id["bank_consistency"].persistent_tag == "consistency_lane"


def test_phase_status_arc_promotion_window_choice_keeps_opportunity_arc_active(bundle, controller_factory) -> None:
    controller = controller_factory(opening_path_id="full_time_work")
    controller.change_career("retail_service")
    controller.state.current_month = 12
    controller.state.player.career.promotion_progress = 6
    controller.state.player.career.promotion_momentum = 62

    event = next(item for item in bundle.events if item.id == "promotion_window")

    resolve_event(bundle, controller.state, event)

    assert len(controller.state.active_status_arcs) == 1
    opening_arc = controller.state.active_status_arcs[0]
    assert opening_arc.arc_id == "promotion_window_open"
    assert opening_arc.source_event_id == "promotion_window"
    opening_months = opening_arc.remaining_months

    controller.resolve_event_choice("push_for_scope")

    assert len(controller.state.active_status_arcs) == 1
    active_arc = controller.state.active_status_arcs[0]
    assert active_arc.arc_id == "promotion_window_open"
    assert active_arc.remaining_months > opening_months
    assert active_arc.severity == 2
    assert "scope_push_lane" in controller.state.player.persistent_tags


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
    push.state.active_modifiers = []
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
    stabilize.state.active_modifiers = []
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
    command.state.active_modifiers = []
    command_ids = {event.id for event in eligible_events(bundle, command.state)}

    coordination = controller_factory(opening_path_id="full_time_work")
    coordination.state.current_month = 24
    coordination.state.player.career.tier_index = 3
    coordination.state.player.career.branch_id = "warehouse_dispatch_track"
    coordination.state.player.transport.reliability_score = 74
    coordination.state.player.social_stability = 60
    resolve_event(bundle, coordination.state, offer)
    coordination.resolve_event_choice("stay_coordination")
    coordination.state.active_modifiers = []
    coordination_ids = {event.id for event in eligible_events(bundle, coordination.state)}

    assert "dispatch_fire_drill" in command_ids
    assert "dispatch_process_upgrade" not in command_ids
    assert "dispatch_process_upgrade" in coordination_ids
    assert "dispatch_fire_drill" not in coordination_ids


def test_second_fork_choices_set_persistent_tags_for_management_and_dispatch(bundle, controller_factory) -> None:
    manager = controller_factory(opening_path_id="full_time_work")
    manager.change_career("retail_service")
    manager.state.current_month = 24
    manager.state.player.career.tier_index = 3
    manager.state.player.career.branch_id = "retail_management_track"
    manager.state.player.social_stability = 64
    manager.state.player.transport.reliability_score = 70

    retail_offer = next(item for item in bundle.events if item.id == "retail_leadership_offer")
    resolve_event(bundle, manager.state, retail_offer)
    manager.resolve_event_choice("take_closing_command")

    second_retail = next(item for item in bundle.events if item.id == "management_overload_wave")
    resolve_event(bundle, manager.state, second_retail)
    manager.resolve_event_choice("absorb_the_wave")
    assert "retail_management_crisis_lead_lane" in manager.state.player.persistent_tags

    dispatch = controller_factory(opening_path_id="full_time_work")
    dispatch.state.current_month = 24
    dispatch.state.player.career.tier_index = 3
    dispatch.state.player.career.branch_id = "warehouse_dispatch_track"
    dispatch.state.player.transport.reliability_score = 74
    dispatch.state.player.social_stability = 60

    dispatch_offer = next(item for item in bundle.events if item.id == "dispatch_lead_offer")
    resolve_event(bundle, dispatch.state, dispatch_offer)
    dispatch.resolve_event_choice("own_the_board")

    second_dispatch = next(item for item in bundle.events if item.id == "dispatch_fire_drill")
    resolve_event(bundle, dispatch.state, second_dispatch)
    dispatch.resolve_event_choice("brute_force_recovery")
    assert "dispatch_escalation_lane" in dispatch.state.player.persistent_tags


def test_management_second_fork_choice_alters_late_event_pool(bundle, controller_factory) -> None:
    overload = controller_factory(opening_path_id="full_time_work")
    overload.change_career("retail_service")
    overload.state.current_month = 32
    overload.state.player.career.tier_index = 3
    overload.state.player.career.branch_id = "retail_management_track"
    overload.state.player.social_stability = 66
    overload.state.player.transport.reliability_score = 72

    leadership_offer = next(item for item in bundle.events if item.id == "retail_leadership_offer")
    resolve_event(bundle, overload.state, leadership_offer)
    overload.resolve_event_choice("take_closing_command")
    overload_wave = next(item for item in bundle.events if item.id == "management_overload_wave")
    resolve_event(bundle, overload.state, overload_wave)
    overload.resolve_event_choice("absorb_the_wave")
    overload.state.active_modifiers = []
    overload_ids = {event.id for event in eligible_events(bundle, overload.state)}

    sustainable = controller_factory(opening_path_id="full_time_work")
    sustainable.change_career("retail_service")
    sustainable.state.current_month = 32
    sustainable.state.player.career.tier_index = 3
    sustainable.state.player.career.branch_id = "retail_management_track"
    sustainable.state.player.social_stability = 66
    sustainable.state.player.transport.reliability_score = 72

    resolve_event(bundle, sustainable.state, leadership_offer)
    sustainable.resolve_event_choice("take_closing_command")
    resolve_event(bundle, sustainable.state, overload_wave)
    sustainable.resolve_event_choice("reset_workload")
    sustainable.state.active_modifiers = []
    sustainable_ids = {event.id for event in eligible_events(bundle, sustainable.state)}

    assert "retail_crisis_lead_backfill_offer" in overload_ids
    assert "retail_sustainable_ops_dividend" not in overload_ids
    assert "retail_sustainable_ops_dividend" in sustainable_ids
    assert "retail_crisis_lead_backfill_offer" not in sustainable_ids


def test_dispatch_second_fork_choice_alters_late_event_pool(bundle, controller_factory) -> None:
    escalation = controller_factory(opening_path_id="full_time_work")
    escalation.state.current_month = 32
    escalation.state.player.career.tier_index = 3
    escalation.state.player.career.branch_id = "warehouse_dispatch_track"
    escalation.state.player.transport.reliability_score = 76
    escalation.state.player.social_stability = 62

    dispatch_offer = next(item for item in bundle.events if item.id == "dispatch_lead_offer")
    resolve_event(bundle, escalation.state, dispatch_offer)
    escalation.resolve_event_choice("own_the_board")
    dispatch_fire = next(item for item in bundle.events if item.id == "dispatch_fire_drill")
    resolve_event(bundle, escalation.state, dispatch_fire)
    escalation.resolve_event_choice("brute_force_recovery")
    escalation.state.active_modifiers = []
    escalation_ids = {event.id for event in eligible_events(bundle, escalation.state)}

    resilient = controller_factory(opening_path_id="full_time_work")
    resilient.state.current_month = 32
    resilient.state.player.career.tier_index = 3
    resilient.state.player.career.branch_id = "warehouse_dispatch_track"
    resilient.state.player.transport.reliability_score = 76
    resilient.state.player.social_stability = 62

    resolve_event(bundle, resilient.state, dispatch_offer)
    resilient.resolve_event_choice("own_the_board")
    resolve_event(bundle, resilient.state, dispatch_fire)
    resilient.resolve_event_choice("protect_shift_reliability")
    resilient.state.active_modifiers = []
    resilient_ids = {event.id for event in eligible_events(bundle, resilient.state)}

    assert "dispatch_escalation_penalty_cycle" in escalation_ids
    assert "dispatch_resilience_compound" not in escalation_ids
    assert "dispatch_resilience_compound" in resilient_ids
    assert "dispatch_escalation_penalty_cycle" not in resilient_ids


def test_office_lane_commitment_choice_alters_future_event_pool(bundle, controller_factory) -> None:
    execution = controller_factory(opening_path_id="full_time_work")
    execution.state.current_month = 24
    execution.state.player.career.track_id = "office_admin"
    execution.state.player.career.tier_index = 3
    execution.state.player.social_stability = 66
    offer = next(item for item in bundle.events if item.id == "office_advancement_charter")
    resolve_event(bundle, execution.state, offer)
    execution.resolve_event_choice("take_operating_scope")
    execution.state.active_modifiers = []
    execution_ids = {event.id for event in eligible_events(bundle, execution.state)}

    consistency = controller_factory(opening_path_id="full_time_work")
    consistency.state.current_month = 24
    consistency.state.player.career.track_id = "office_admin"
    consistency.state.player.career.tier_index = 3
    consistency.state.player.social_stability = 66
    resolve_event(bundle, consistency.state, offer)
    consistency.resolve_event_choice("bank_operating_consistency")
    consistency.state.active_modifiers = []
    consistency_ids = {event.id for event in eligible_events(bundle, consistency.state)}

    assert "office_scope_overflow_wave" in execution_ids
    assert "office_consistency_flywheel" not in execution_ids
    assert "office_consistency_flywheel" in consistency_ids
    assert "office_scope_overflow_wave" not in consistency_ids


@pytest.mark.parametrize(
    ("track_id", "branch_id", "event_id", "choice_id", "expected_tag"),
    [
        ("retail_service", "retail_sales_track", "sales_territory_offer", "go_full_commission", "retail_sales_commission_lane"),
        ("retail_service", "retail_sales_track", "sales_territory_offer", "take_salary_plus_bonus", "retail_sales_book_builder_lane"),
        ("warehouse_logistics", "warehouse_ops_track", "warehouse_foreman_offer", "take_foreman_role", "warehouse_foreman_command_lane"),
        ("warehouse_logistics", "warehouse_ops_track", "warehouse_foreman_offer", "stay_floor_anchor", "warehouse_floor_anchor_lane"),
        ("warehouse_logistics", "warehouse_equipment_track", "equipment_specialist_offer", "accept_specialist_rotation", "warehouse_equipment_specialist_lane"),
        ("warehouse_logistics", "warehouse_equipment_track", "equipment_specialist_offer", "stay_current_floor", "warehouse_equipment_stability_lane"),
        ("office_admin", "office_people_track", "office_team_retention_wave", "bank_morale", "office_people_culture_lane"),
        ("office_admin", "office_people_track", "office_team_retention_wave", "push_output_window", "office_people_output_lane"),
        ("office_admin", "office_compliance_track", "office_audit_window", "lock_controls", "office_compliance_control_lane"),
        ("office_admin", "office_compliance_track", "office_audit_window", "optimize_controls", "office_compliance_efficiency_lane"),
    ],
)
def test_branch_offer_choices_set_persistent_tags_for_weaker_branch_futures(
    bundle, controller_factory, track_id, branch_id, event_id, choice_id, expected_tag
) -> None:
    controller = controller_factory(opening_path_id="full_time_work")
    _seed_branch_offer_state(controller, track_id=track_id, branch_id=branch_id)

    offer = next(item for item in bundle.events if item.id == event_id)
    resolve_event(bundle, controller.state, offer)
    controller.resolve_event_choice(choice_id)

    assert expected_tag in controller.state.player.persistent_tags


@pytest.mark.parametrize(
    (
        "track_id",
        "branch_id",
        "event_id",
        "choice_a",
        "choice_b",
        "expected_event_a",
        "expected_event_b",
    ),
    [
        (
            "retail_service",
            "retail_sales_track",
            "sales_territory_offer",
            "go_full_commission",
            "take_salary_plus_bonus",
            "retail_sales_commission_cycle",
            "retail_sales_book_dividend",
        ),
        (
            "warehouse_logistics",
            "warehouse_ops_track",
            "warehouse_foreman_offer",
            "take_foreman_role",
            "stay_floor_anchor",
            "warehouse_foreman_bottleneck_cycle",
            "warehouse_floor_anchor_dividend",
        ),
        (
            "warehouse_logistics",
            "warehouse_equipment_track",
            "equipment_specialist_offer",
            "accept_specialist_rotation",
            "stay_current_floor",
            "equipment_specialist_backlog_cycle",
            "equipment_reliability_dividend",
        ),
        (
            "office_admin",
            "office_people_track",
            "office_team_retention_wave",
            "push_output_window",
            "bank_morale",
            "office_people_output_backlash",
            "office_people_culture_dividend",
        ),
        (
            "office_admin",
            "office_compliance_track",
            "office_audit_window",
            "optimize_controls",
            "lock_controls",
            "office_compliance_exception_cycle",
            "office_compliance_control_dividend",
        ),
    ],
)
def test_weaker_branch_offer_choices_open_distinct_late_followup_event_pools(
    bundle,
    controller_factory,
    track_id,
    branch_id,
    event_id,
    choice_a,
    choice_b,
    expected_event_a,
    expected_event_b,
) -> None:
    first = controller_factory(opening_path_id="full_time_work")
    second = controller_factory(opening_path_id="full_time_work")
    _seed_branch_offer_state(first, track_id=track_id, branch_id=branch_id, month=32)
    _seed_branch_offer_state(second, track_id=track_id, branch_id=branch_id, month=32)

    offer = next(item for item in bundle.events if item.id == event_id)
    resolve_event(bundle, first.state, offer)
    first.resolve_event_choice(choice_a)
    first.state.active_modifiers = []
    first_ids = {event.id for event in eligible_events(bundle, first.state)}

    resolve_event(bundle, second.state, offer)
    second.resolve_event_choice(choice_b)
    second.state.active_modifiers = []
    second_ids = {event.id for event in eligible_events(bundle, second.state)}

    assert expected_event_a in first_ids
    assert expected_event_b not in first_ids
    assert expected_event_b in second_ids
    assert expected_event_a not in second_ids


@pytest.mark.parametrize(
    ("track_id", "branch_id", "event_id", "choice_id", "expected_tag"),
    [
        ("delivery_gig", "delivery_route_grind_track", "delivery_route_crush_week", "stack_the_route", "delivery_route_overdrive_lane"),
        ("delivery_gig", "delivery_route_grind_track", "delivery_route_crush_week", "protect_the_vehicle", "delivery_vehicle_buffer_lane"),
        (
            "delivery_gig",
            "delivery_independent_operator_track",
            "delivery_operator_contract_bid",
            "keep_operator_flexible",
            "delivery_flex_buffer_lane",
        ),
        ("trades_apprenticeship", "trades_field_crew_track", "trades_field_crew_weather_crunch", "push_the_crew_day", "trades_field_push_lane"),
        ("trades_apprenticeship", "trades_field_crew_track", "trades_field_crew_weather_crunch", "protect_the_pace", "trades_field_recovery_lane"),
        (
            "trades_apprenticeship",
            "trades_estimator_supervisor_track",
            "trades_scope_change_order_wave",
            "own_the_change_orders",
            "trades_scope_surge_lane",
        ),
        (
            "trades_apprenticeship",
            "trades_estimator_supervisor_track",
            "trades_scope_change_order_wave",
            "stabilize_the_scope",
            "trades_scope_anchor_lane",
        ),
        (
            "healthcare_support",
            "healthcare_floor_care_track",
            "healthcare_floor_care_double_shift",
            "cover_the_floor_gap",
            "healthcare_floor_gap_lane",
        ),
        (
            "healthcare_support",
            "healthcare_floor_care_track",
            "healthcare_floor_care_double_shift",
            "protect_shift_recovery",
            "healthcare_floor_recovery_lane",
        ),
        (
            "healthcare_support",
            "healthcare_scheduling_coordination_track",
            "healthcare_schedule_gap_cascade",
            "triage_the_gap_board",
            "healthcare_schedule_triage_lane",
        ),
        (
            "healthcare_support",
            "healthcare_scheduling_coordination_track",
            "healthcare_schedule_gap_cascade",
            "protect_team_stability",
            "healthcare_schedule_stability_lane",
        ),
    ],
)
def test_delivery_trades_healthcare_branch_choices_set_persistent_tags(
    bundle, controller_factory, track_id, branch_id, event_id, choice_id, expected_tag
) -> None:
    controller = controller_factory(opening_path_id="full_time_work")
    _seed_branch_offer_state(controller, track_id=track_id, branch_id=branch_id)

    offer = next(item for item in bundle.events if item.id == event_id)
    resolve_event(bundle, controller.state, offer)
    controller.resolve_event_choice(choice_id)

    assert expected_tag in controller.state.player.persistent_tags


@pytest.mark.parametrize(
    (
        "track_id",
        "branch_id",
        "event_id",
        "choice_a",
        "choice_b",
        "expected_event_a",
        "expected_event_b",
    ),
    [
        (
            "delivery_gig",
            "delivery_route_grind_track",
            "delivery_route_crush_week",
            "stack_the_route",
            "protect_the_vehicle",
            "delivery_route_overdrive_cycle",
            "delivery_vehicle_buffer_dividend",
        ),
        (
            "delivery_gig",
            "delivery_independent_operator_track",
            "delivery_operator_contract_bid",
            "bid_for_scope",
            "keep_operator_flexible",
            "delivery_surge_scope_backlash",
            "delivery_flexible_operator_dividend",
        ),
        (
            "trades_apprenticeship",
            "trades_field_crew_track",
            "trades_field_crew_weather_crunch",
            "push_the_crew_day",
            "protect_the_pace",
            "trades_field_pushback_cycle",
            "trades_field_recovery_dividend",
        ),
        (
            "trades_apprenticeship",
            "trades_estimator_supervisor_track",
            "trades_scope_change_order_wave",
            "own_the_change_orders",
            "stabilize_the_scope",
            "trades_scope_overrun_cycle",
            "trades_scope_anchor_dividend",
        ),
        (
            "healthcare_support",
            "healthcare_floor_care_track",
            "healthcare_floor_care_double_shift",
            "cover_the_floor_gap",
            "protect_shift_recovery",
            "healthcare_floor_gap_aftershock",
            "healthcare_floor_recovery_dividend",
        ),
        (
            "healthcare_support",
            "healthcare_scheduling_coordination_track",
            "healthcare_schedule_gap_cascade",
            "triage_the_gap_board",
            "protect_team_stability",
            "healthcare_schedule_exception_cycle",
            "healthcare_schedule_stability_dividend",
        ),
    ],
)
def test_delivery_trades_healthcare_branch_choices_open_distinct_late_followups(
    bundle,
    controller_factory,
    track_id,
    branch_id,
    event_id,
    choice_a,
    choice_b,
    expected_event_a,
    expected_event_b,
) -> None:
    first = controller_factory(opening_path_id="full_time_work")
    second = controller_factory(opening_path_id="full_time_work")
    _seed_branch_offer_state(first, track_id=track_id, branch_id=branch_id, month=32)
    _seed_branch_offer_state(second, track_id=track_id, branch_id=branch_id, month=32)

    offer = next(item for item in bundle.events if item.id == event_id)
    resolve_event(bundle, first.state, offer)
    first.resolve_event_choice(choice_a)
    first.state.active_modifiers = []
    first_ids = {event.id for event in eligible_events(bundle, first.state)}

    resolve_event(bundle, second.state, offer)
    second.resolve_event_choice(choice_b)
    second.state.active_modifiers = []
    second_ids = {event.id for event in eligible_events(bundle, second.state)}

    assert expected_event_a in first_ids
    assert expected_event_b not in first_ids
    assert expected_event_b in second_ids
    assert expected_event_a not in second_ids


def test_healthcare_lane_commitment_choice_alters_future_event_pool(bundle, controller_factory) -> None:
    command = controller_factory(opening_path_id="full_time_work")
    command.state.current_month = 24
    command.state.player.career.track_id = "healthcare_support"
    command.state.player.career.tier_index = 3
    command.state.player.social_stability = 64
    offer = next(item for item in bundle.events if item.id == "healthcare_shift_lead_offer")
    resolve_event(bundle, command.state, offer)
    command.resolve_event_choice("take_triage_command")
    command.state.active_modifiers = []
    command_ids = {event.id for event in eligible_events(bundle, command.state)}

    continuity = controller_factory(opening_path_id="full_time_work")
    continuity.state.current_month = 24
    continuity.state.player.career.track_id = "healthcare_support"
    continuity.state.player.career.tier_index = 3
    continuity.state.player.social_stability = 64
    resolve_event(bundle, continuity.state, offer)
    continuity.resolve_event_choice("protect_care_continuity")
    continuity.state.active_modifiers = []
    continuity_ids = {event.id for event in eligible_events(bundle, continuity.state)}

    assert "healthcare_triage_surge" in command_ids
    assert "healthcare_continuity_protocol_win" not in command_ids
    assert "healthcare_continuity_protocol_win" in continuity_ids
    assert "healthcare_triage_surge" not in continuity_ids


def test_trades_lane_commitment_choice_alters_future_event_pool(bundle, controller_factory) -> None:
    expansion = controller_factory(opening_path_id="full_time_work")
    expansion.state.current_month = 24
    expansion.state.player.career.track_id = "trades_apprenticeship"
    expansion.state.player.career.tier_index = 3
    expansion.state.player.transport.reliability_score = 74
    offer = next(item for item in bundle.events if item.id == "trades_crew_lead_offer")
    resolve_event(bundle, expansion.state, offer)
    expansion.resolve_event_choice("take_emergency_call_rotation")
    expansion.state.active_modifiers = []
    expansion_ids = {event.id for event in eligible_events(bundle, expansion.state)}

    precision = controller_factory(opening_path_id="full_time_work")
    precision.state.current_month = 24
    precision.state.player.career.track_id = "trades_apprenticeship"
    precision.state.player.career.tier_index = 3
    precision.state.player.transport.reliability_score = 74
    resolve_event(bundle, precision.state, offer)
    precision.resolve_event_choice("anchor_precision_schedule")
    precision.state.active_modifiers = []
    precision_ids = {event.id for event in eligible_events(bundle, precision.state)}

    assert "trades_emergency_callout_wave" in expansion_ids
    assert "trades_quality_contract_pipeline" not in expansion_ids
    assert "trades_quality_contract_pipeline" in precision_ids
    assert "trades_emergency_callout_wave" not in precision_ids


def test_persistent_career_tag_is_saved_on_choice(bundle, controller_factory) -> None:
    controller = controller_factory()
    event = next(item for item in bundle.events if item.id == "promotion_window")

    resolve_event(bundle, controller.state, event)
    controller.resolve_event_choice("push_for_scope")

    assert "scope_push_lane" in controller.state.player.persistent_tags


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


def test_phase7_top_victory_requires_branch_identity_even_with_money(controller_factory) -> None:
    controller = controller_factory(opening_path_id="full_time_work")
    player = controller.state.player
    player.cash = 180_000
    player.savings = 35_000
    player.high_interest_savings = 12_000
    player.index_fund = 20_000
    player.aggressive_growth_fund = 8_000
    player.debt = 0
    player.credit_score = 760
    player.housing.housing_stability = 82
    player.social_stability = 74
    player.monthly_surplus = 700
    player.stress = 28
    player.energy = 82
    player.career.track_id = "warehouse_logistics"
    player.career.tier_index = 4
    player.career.branch_id = None

    without_branch_ids = {win_state.id for win_state in controller.available_win_states()}
    assert "financial_anchor" not in without_branch_ids

    player.career.branch_id = "warehouse_dispatch_track"
    with_branch_ids = {win_state.id for win_state in controller.available_win_states()}
    assert "financial_anchor" in with_branch_ids


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
