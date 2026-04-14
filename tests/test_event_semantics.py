from __future__ import annotations

from random import Random

import pytest

from budgetwars.engine.events import resolve_event, resolve_event_choice
from budgetwars.engine.month_resolution import resolve_month
from budgetwars.engine.scoring import build_live_score_snapshot


def test_take_real_recovery_materially_repairs_body_state(bundle, controller_factory):
    controller = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")
    state = controller.state
    state.current_month = 10
    state.player.selected_focus_action_id = "overtime"
    state.player.stress = 78
    state.player.energy = 28
    state.player.cash = 900
    state.player.savings = 300

    burnout = next(event for event in bundle.events if event.id == "burnout_month")

    resolve_event(bundle, state, burnout)
    before_stress = state.player.stress
    before_energy = state.player.energy

    resolve_event_choice(bundle, state, "burnout_month", "take_real_recovery")

    assert state.player.stress <= before_stress - 4
    assert state.player.energy >= before_energy + 4


def test_rebalance_workload_is_meaningful_relief(bundle, controller_factory):
    controller = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")
    state = controller.state
    state.current_month = 9
    state.player.selected_focus_action_id = "overtime"
    state.player.stress = 74
    state.player.energy = 34

    attrition = next(event for event in bundle.events if event.id == "overtime_attrition_warning")

    resolve_event(bundle, state, attrition)
    before_stress = state.player.stress

    resolve_event_choice(bundle, state, "overtime_attrition_warning", "rebalance_workload")

    assert state.player.stress <= before_stress - 4
    burnout_arc = next(arc for arc in state.active_status_arcs if arc.arc_id == "burnout_risk")
    assert burnout_arc.severity == 1


def test_refinance_now_relieves_pressure_and_improves_next_month_score(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    refinance = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    wait = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")

    for controller in (refinance, wait):
        state = controller.state
        state.current_month = 12
        state.player.debt = 6000
        state.player.credit_score = 720
        state.player.cash = 180
        state.player.savings = 200
        state.player.stress = 66
        state.player.energy = 48

    event = next(item for item in bundle.events if item.id == "refinance_window")

    resolve_event(bundle, refinance.state, event)
    before_stress = refinance.state.player.stress
    resolve_event_choice(bundle, refinance.state, "refinance_window", "refinance_now")

    resolve_event(bundle, wait.state, event)
    resolve_event_choice(bundle, wait.state, "refinance_window", "wait_for_better_rate")

    assert refinance.state.player.stress <= before_stress

    resolve_month(quiet_bundle, refinance.state, Random(42))
    resolve_month(quiet_bundle, wait.state, Random(42))

    refinance_score = build_live_score_snapshot(quiet_bundle, refinance.state).projected_score
    wait_score = build_live_score_snapshot(quiet_bundle, wait.state).projected_score

    assert refinance_score >= wait_score + 3.0


@pytest.mark.parametrize(
    ("track_id", "branch_id", "event_id", "stabilize_choice", "push_choice", "modifier_id", "persistent_tag"),
    [
        (
            "retail_service",
            "retail_management_track",
            "retail_leadership_offer",
            "stabilize_the_floor",
            "take_closing_command",
            "retail_rhythm",
            "retail_management_stability_lane",
        ),
        (
            "healthcare_support",
            "healthcare_floor_care_track",
            "healthcare_shift_lead_offer",
            "protect_care_continuity",
            "take_triage_command",
            "care_continuity_rhythm",
            "healthcare_continuity_lane",
        ),
    ],
)
def test_branch_stabilizers_protect_body_state_and_next_month_score(
    bundle,
    controller_factory,
    track_id,
    branch_id,
    event_id,
    stabilize_choice,
    push_choice,
    modifier_id,
    persistent_tag,
):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    stabilize = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")
    push = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")

    for controller in (stabilize, push):
        state = controller.state
        state.current_month = 20
        state.player.career.track_id = track_id
        state.player.career.branch_id = branch_id
        state.player.career.tier_index = 3
        state.player.social_stability = 62
        state.player.stress = 62
        state.player.energy = 50
        state.player.cash = 1200
        state.player.savings = 700

    event = next(item for item in bundle.events if item.id == event_id)

    resolve_event(bundle, stabilize.state, event)
    before_stress = stabilize.state.player.stress
    resolve_event_choice(bundle, stabilize.state, event_id, stabilize_choice)

    resolve_event(bundle, push.state, event)
    resolve_event_choice(bundle, push.state, event_id, push_choice)

    assert stabilize.state.player.stress <= before_stress
    assert any(modifier.id == modifier_id for modifier in stabilize.state.active_modifiers)
    assert persistent_tag in stabilize.state.player.persistent_tags

    resolve_month(quiet_bundle, stabilize.state, Random(42))
    resolve_month(quiet_bundle, push.state, Random(42))

    stabilize_score = build_live_score_snapshot(quiet_bundle, stabilize.state).projected_score
    push_score = build_live_score_snapshot(quiet_bundle, push.state).projected_score

    assert stabilize_score >= push_score + 1.0


@pytest.mark.parametrize(
    ("track_id", "branch_id", "event_id", "protect_choice", "push_choice", "modifier_id", "persistent_tag"),
    [
        (
            "retail_service",
            "retail_management_track",
            "retail_inventory_crunch",
            "protect_the_team",
            "cover_the_floor",
            "retail_team_reset",
            "retail_team_protection_lane",
        ),
        (
            "warehouse_logistics",
            "warehouse_ops_track",
            "dock_bottleneck",
            "run_a_safer_shift",
            "stay_late",
            "warehouse_safe_shift_rhythm",
            "warehouse_safe_shift_lane",
        ),
    ],
)
def test_branch_protective_choices_create_real_stabilizer_lanes(
    bundle,
    controller_factory,
    track_id,
    branch_id,
    event_id,
    protect_choice,
    push_choice,
    modifier_id,
    persistent_tag,
):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    protect = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")
    push = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")

    for controller in (protect, push):
        state = controller.state
        state.current_month = 9
        state.player.career.track_id = track_id
        state.player.career.branch_id = branch_id
        state.player.career.tier_index = 2
        state.player.social_stability = 58
        state.player.stress = 64
        state.player.energy = 46
        state.player.cash = 900
        state.player.savings = 350

    event = next(item for item in bundle.events if item.id == event_id)

    resolve_event(bundle, protect.state, event)
    before_stress = protect.state.player.stress
    before_energy = protect.state.player.energy
    resolve_event_choice(bundle, protect.state, event_id, protect_choice)

    resolve_event(bundle, push.state, event)
    resolve_event_choice(bundle, push.state, event_id, push_choice)

    assert protect.state.player.stress <= before_stress
    assert protect.state.player.energy >= before_energy
    assert any(modifier.id == modifier_id for modifier in protect.state.active_modifiers)
    assert persistent_tag in protect.state.player.persistent_tags

    resolve_month(quiet_bundle, protect.state, Random(42))
    resolve_month(quiet_bundle, push.state, Random(42))

    protect_score = build_live_score_snapshot(quiet_bundle, protect.state).projected_score
    push_score = build_live_score_snapshot(quiet_bundle, push.state).projected_score

    assert protect_score >= push_score + 1.0


def test_lease_survival_choices_lower_pressure_and_create_distinct_futures(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    hold = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    downgrade = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")

    for controller in (hold, downgrade):
        state = controller.state
        state.current_month = 12
        state.player.housing.option_id = "solo_rental"
        state.player.housing.housing_stability = 34
        state.player.credit_score = 610
        state.player.cash = 140
        state.player.savings = 0
        state.player.monthly_surplus = -220
        state.player.stress = 74
        state.player.energy = 40

    event = next(item for item in bundle.events if item.id == "lease_enforcement_notice")

    resolve_event(bundle, hold.state, event)
    hold_before_stress = hold.state.player.stress
    resolve_event_choice(bundle, hold.state, "lease_enforcement_notice", "pay_to_hold_lease")

    resolve_event(bundle, downgrade.state, event)
    downgrade_before_stress = downgrade.state.player.stress
    resolve_event_choice(bundle, downgrade.state, "lease_enforcement_notice", "plan_fast_downgrade")

    assert hold.state.player.stress <= hold_before_stress
    assert downgrade.state.player.stress <= downgrade_before_stress
    assert any(arc.arc_id == "lease_pressure" for arc in hold.state.active_status_arcs)
    assert not any(arc.arc_id == "lease_pressure" for arc in downgrade.state.active_status_arcs)

    resolve_month(quiet_bundle, hold.state, Random(42))
    resolve_month(quiet_bundle, downgrade.state, Random(42))

    hold_score = build_live_score_snapshot(quiet_bundle, hold.state).projected_score
    downgrade_score = build_live_score_snapshot(quiet_bundle, downgrade.state).projected_score

    assert downgrade_score >= hold_score + 1.0


def test_delay_the_move_no_longer_adds_extra_stress(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    state = controller.state
    state.current_month = 11
    state.player.housing.option_id = "roommates"
    state.player.credit_score = 590
    state.player.debt = 4200
    state.player.stress = 63
    state.player.energy = 44

    event = next(item for item in bundle.events if item.id == "security_deposit_shock")

    resolve_event(bundle, state, event)
    before_stress = state.player.stress

    resolve_event_choice(bundle, state, "security_deposit_shock", "delay_the_move")

    assert state.player.stress <= before_stress
