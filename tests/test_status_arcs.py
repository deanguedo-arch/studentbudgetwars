from __future__ import annotations

from budgetwars.engine.status_arcs import (
    refresh_status_arc,
    resolve_status_arc,
    start_status_arc,
    tick_status_arcs,
)
from budgetwars.engine.events import resolve_event, resolve_event_choice


def test_start_status_arc_creates_named_arc(bundle, controller_factory):
    controller = controller_factory()

    start_status_arc(
        bundle,
        controller.state,
        "transport_unstable",
        source_event_id="car_repair",
        duration_months=3,
        severity=1,
        note="Repair bill landed.",
    )

    assert len(controller.state.active_status_arcs) == 1
    arc = controller.state.active_status_arcs[0]
    assert arc.arc_id == "transport_unstable"
    assert arc.source_event_id == "car_repair"
    assert arc.remaining_months == 3
    assert arc.severity == 1
    assert arc.started_month == controller.state.current_month
    assert arc.note == "Repair bill landed."


def test_start_status_arc_refreshes_existing_arc_instead_of_duplicating(bundle, controller_factory):
    controller = controller_factory()

    start_status_arc(
        bundle,
        controller.state,
        "transport_unstable",
        source_event_id="car_repair",
        duration_months=3,
        severity=1,
        note="First hit.",
    )
    start_status_arc(
        bundle,
        controller.state,
        "transport_unstable",
        source_event_id="beater_breakdown",
        duration_months=2,
        severity=2,
        note="Second hit.",
    )

    assert len(controller.state.active_status_arcs) == 1
    arc = controller.state.active_status_arcs[0]
    assert arc.source_event_id == "beater_breakdown"
    assert arc.remaining_months == 5
    assert arc.severity == 2
    assert arc.note == "Second hit."


def test_refresh_status_arc_caps_severity_at_three(bundle, controller_factory):
    controller = controller_factory()

    start_status_arc(
        bundle,
        controller.state,
        "credit_squeeze",
        source_event_id="collections_warning",
        duration_months=2,
        severity=2,
    )
    refresh_status_arc(
        controller.state,
        "credit_squeeze",
        duration_months=2,
        severity_delta=2,
        note="Pressure worsened.",
    )

    arc = controller.state.active_status_arcs[0]
    assert arc.remaining_months == 4
    assert arc.severity == 3
    assert arc.note == "Pressure worsened."


def test_resolve_status_arc_removes_arc(bundle, controller_factory):
    controller = controller_factory()

    start_status_arc(
        bundle,
        controller.state,
        "education_slipping",
        source_event_id="overtime_exam_collision",
        duration_months=3,
        severity=1,
    )

    resolve_status_arc(controller.state, "education_slipping")

    assert controller.state.active_status_arcs == []


def test_tick_status_arcs_decrements_and_expires(bundle, controller_factory):
    controller = controller_factory()

    start_status_arc(
        bundle,
        controller.state,
        "transport_unstable",
        source_event_id="car_repair",
        duration_months=2,
        severity=1,
    )

    tick_status_arcs(bundle, controller.state)
    assert controller.state.active_status_arcs[0].remaining_months == 1

    tick_status_arcs(bundle, controller.state)
    assert controller.state.active_status_arcs == []


def test_beater_total_failure_escalates_transport_arc_and_miss_shift_choice_keeps_it_live(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    state = controller.state
    state.player.transport.option_id = "beater_car"
    state.player.transport.reliability_score = 34

    start_status_arc(
        bundle,
        state,
        "transport_unstable",
        source_event_id="beater_breakdown",
        duration_months=2,
        severity=2,
        note="The commute is already shaky.",
    )
    total_failure = next(item for item in bundle.events if item.id == "beater_total_failure")

    resolve_event(bundle, state, total_failure)

    arc = state.active_status_arcs[0]
    assert state.pending_user_choice_event_id == "beater_total_failure"
    assert arc.arc_id == "transport_unstable"
    assert arc.severity == 3
    months_after_failure = arc.remaining_months

    resolve_event_choice(bundle, state, "beater_total_failure", "miss_shift_block")

    arc = state.active_status_arcs[0]
    assert arc.severity == 3
    assert arc.remaining_months > months_after_failure


def test_lease_enforcement_downgrade_choice_resolves_lease_pressure(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    state = controller.state
    state.player.housing.option_id = "solo_rental"
    state.player.housing.housing_stability = 34

    start_status_arc(
        bundle,
        state,
        "lease_pressure",
        source_event_id="lease_default_warning",
        duration_months=3,
        severity=2,
    )
    enforcement = next(item for item in bundle.events if item.id == "lease_enforcement_notice")

    resolve_event(bundle, state, enforcement)
    resolve_event_choice(bundle, state, "lease_enforcement_notice", "plan_fast_downgrade")

    assert not state.active_status_arcs


def test_burnout_month_choices_create_real_recovery_fork(bundle, controller_factory):
    recovery = controller_factory(opening_path_id="full_time_work")
    mask = controller_factory(opening_path_id="full_time_work")

    for controller in (recovery, mask):
        start_status_arc(
            bundle,
            controller.state,
            "burnout_risk",
            source_event_id="overtime_attrition_warning",
            duration_months=2,
            severity=2,
        )
        controller.state.player.stress = 76
        controller.state.player.energy = 28

    burnout_event = next(item for item in bundle.events if item.id == "burnout_month")
    choice_ids = {choice.id for choice in burnout_event.choices}

    assert {"take_real_recovery", "mask_and_push"} <= choice_ids

    resolve_event(bundle, recovery.state, burnout_event)
    resolve_event_choice(bundle, recovery.state, "burnout_month", "take_real_recovery")

    resolve_event(bundle, mask.state, burnout_event)
    resolve_event_choice(bundle, mask.state, "burnout_month", "mask_and_push")

    recovery_arc = recovery.state.active_status_arcs[0]
    mask_arc = mask.state.active_status_arcs[0]
    assert recovery_arc.severity == 1
    assert mask_arc.severity == 3
