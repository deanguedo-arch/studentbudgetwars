from __future__ import annotations

from budgetwars.engine.status_arcs import (
    refresh_status_arc,
    resolve_status_arc,
    start_status_arc,
    tick_status_arcs,
)


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
