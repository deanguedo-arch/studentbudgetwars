from __future__ import annotations

from budgetwars.models import ActiveStatusArc, ContentBundle, GameState


def _arc_definition(bundle: ContentBundle, arc_id: str):
    for arc in bundle.status_arcs:
        if arc.id == arc_id:
            return arc
    raise ValueError(f"Unknown status arc: {arc_id}")


def _active_arc(state: GameState, arc_id: str) -> ActiveStatusArc | None:
    return next((arc for arc in state.active_status_arcs if arc.arc_id == arc_id), None)


def start_status_arc(
    bundle: ContentBundle,
    state: GameState,
    arc_id: str,
    *,
    source_event_id: str,
    duration_months: int | None = None,
    severity: int = 1,
    note: str | None = None,
    followup_pending: bool = False,
) -> ActiveStatusArc:
    definition = _arc_definition(bundle, arc_id)
    duration = duration_months if duration_months is not None else definition.default_duration_months
    existing = _active_arc(state, arc_id)
    if existing is not None:
        existing.source_event_id = source_event_id
        existing.remaining_months += max(0, duration)
        existing.severity = min(3, max(existing.severity, severity))
        if note is not None:
            existing.note = note
        existing.followup_pending = existing.followup_pending or followup_pending
        return existing

    active = ActiveStatusArc(
        arc_id=arc_id,
        source_event_id=source_event_id,
        remaining_months=max(0, duration),
        severity=max(1, min(3, severity)),
        started_month=state.current_month,
        followup_pending=followup_pending,
        note=note,
    )
    state.active_status_arcs.append(active)
    return active


def refresh_status_arc(
    state: GameState,
    arc_id: str,
    *,
    duration_months: int = 0,
    severity_delta: int = 0,
    note: str | None = None,
    followup_pending: bool | None = None,
) -> ActiveStatusArc:
    active = _active_arc(state, arc_id)
    if active is None:
        raise ValueError(f"Status arc is not active: {arc_id}")
    active.remaining_months += max(0, duration_months)
    active.severity = min(3, max(1, active.severity + severity_delta))
    if note is not None:
        active.note = note
    if followup_pending is not None:
        active.followup_pending = followup_pending
    return active


def resolve_status_arc(state: GameState, arc_id: str) -> None:
    state.active_status_arcs = [arc for arc in state.active_status_arcs if arc.arc_id != arc_id]


def tick_status_arcs(bundle: ContentBundle, state: GameState) -> None:
    del bundle
    remaining: list[ActiveStatusArc] = []
    for arc in state.active_status_arcs:
        arc.remaining_months = max(0, arc.remaining_months - 1)
        if arc.remaining_months > 0:
            remaining.append(arc)
    state.active_status_arcs = remaining
