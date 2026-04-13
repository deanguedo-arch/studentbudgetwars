from __future__ import annotations

from budgetwars.models import ActiveStatusArc, ContentBundle, GameState


_EVENT_START_RULES = {
    "car_repair": {
        "arc_id": "transport_unstable",
        "duration_months": 2,
        "severity": 1,
        "note": "Repair bills are turning transport into a live problem.",
    },
    "beater_breakdown": {
        "arc_id": "transport_unstable",
        "duration_months": 3,
        "severity": 2,
        "note": "A breakdown turned transport into an ongoing risk.",
    },
    "beater_cascade_choice": {
        "arc_id": "transport_unstable",
        "duration_months": 3,
        "severity": 2,
        "note": "The beater is now a month-shaping fragility problem.",
    },
    "missed_shift_after_breakdown": {
        "arc_id": "transport_unstable",
        "duration_months": 2,
        "severity": 2,
        "note": "Transport instability has already started costing real work.",
    },
    "collections_warning": {
        "arc_id": "credit_squeeze",
        "duration_months": 4,
        "severity": 2,
        "note": "Credit pressure is now shaping future doors and penalties.",
    },
    "credit_limit_review": {
        "arc_id": "credit_squeeze",
        "duration_months": 3,
        "severity": 2,
        "note": "Your file is under review and weak cleanup will keep shrinking options.",
    },
}

_CHOICE_RULES = {
    ("beater_cascade_choice", "eat_the_upgrade_hit"): {
        "action": "resolve",
        "arc_id": "transport_unstable",
    },
    ("credit_limit_review", "tighten_up"): {
        "action": "refresh",
        "arc_id": "credit_squeeze",
        "duration_months": 1,
        "severity_delta": -1,
        "note": "You are containing the squeeze, but it is not gone yet.",
    },
    ("credit_limit_review", "coast"): {
        "action": "refresh",
        "arc_id": "credit_squeeze",
        "duration_months": 2,
        "severity_delta": 1,
        "note": "Credit pressure is worsening because you chose breathing room over cleanup.",
    },
    ("credit_rebuild_window", "open_the_secured_line"): {
        "action": "refresh",
        "arc_id": "credit_squeeze",
        "duration_months": 1,
        "severity_delta": -1,
        "note": "The rebuild lane is starting to soften the squeeze.",
    },
    ("refinance_window", "refinance_now"): {
        "action": "resolve",
        "arc_id": "credit_squeeze",
    },
}


def _arc_definition(bundle: ContentBundle, arc_id: str):
    for arc in bundle.status_arcs:
        if arc.id == arc_id:
            return arc
    raise ValueError(f"Unknown status arc: {arc_id}")


def _active_arc(state: GameState, arc_id: str) -> ActiveStatusArc | None:
    return next((arc for arc in state.active_status_arcs if arc.arc_id == arc_id), None)


def get_active_status_arc(state: GameState, arc_id: str) -> ActiveStatusArc | None:
    return _active_arc(state, arc_id)


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


def apply_event_status_arc(bundle: ContentBundle, state: GameState, event_id: str) -> ActiveStatusArc | None:
    rule = _EVENT_START_RULES.get(event_id)
    if rule is None:
        return None
    return start_status_arc(
        bundle,
        state,
        rule["arc_id"],
        source_event_id=event_id,
        duration_months=rule["duration_months"],
        severity=rule["severity"],
        note=rule["note"],
    )


def apply_choice_status_arc_resolution(state: GameState, event_id: str, choice_id: str) -> bool:
    rule = _CHOICE_RULES.get((event_id, choice_id))
    if rule is None:
        return False
    if rule["action"] == "resolve":
        resolve_status_arc(state, rule["arc_id"])
        return True
    if rule["action"] == "refresh":
        refresh_status_arc(
            state,
            rule["arc_id"],
            duration_months=rule.get("duration_months", 0),
            severity_delta=rule.get("severity_delta", 0),
            note=rule.get("note"),
        )
        return True
    return True


def status_arc_event_weight_multiplier(state: GameState, event_id: str) -> float:
    multiplier = 1.0
    transport_arc = get_active_status_arc(state, "transport_unstable")
    if transport_arc is not None:
        severity_bonus = 0.1 * transport_arc.severity
        if event_id == "missed_shift_after_breakdown":
            multiplier *= 1.15 + severity_bonus
        elif event_id == "beater_cascade_choice":
            multiplier *= 1.1 + severity_bonus
        elif event_id == "beater_total_failure":
            multiplier *= 1.08 + severity_bonus
        elif event_id == "used_car_window":
            multiplier *= 1.02 + (0.06 * transport_arc.severity)
    credit_arc = get_active_status_arc(state, "credit_squeeze")
    if credit_arc is not None:
        severity_bonus = 0.08 * credit_arc.severity
        if event_id == "collections_warning":
            multiplier *= 1.12 + severity_bonus
        elif event_id == "credit_limit_review":
            multiplier *= 1.15 + severity_bonus
        elif event_id == "credit_rebuild_window":
            multiplier *= 1.02 + (0.05 * credit_arc.severity)
        elif event_id == "refinance_window":
            multiplier *= 1.03 + (0.04 * credit_arc.severity)
    return multiplier
