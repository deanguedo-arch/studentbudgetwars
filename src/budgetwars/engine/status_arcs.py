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
    "beater_total_failure": {
        "arc_id": "transport_unstable",
        "duration_months": 4,
        "severity": 3,
        "note": "Transport failure is now the shape of the month, not a side problem.",
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
    "debt_fee_stack": {
        "arc_id": "credit_squeeze",
        "duration_months": 3,
        "severity": 3,
        "note": "Fee stacking turned credit pressure into direct monthly punishment.",
    },
    "overtime_exam_collision": {
        "arc_id": "education_slipping",
        "duration_months": 3,
        "severity": 2,
        "note": "Work-school conflict is now dragging the academic lane.",
    },
    "exam_probation_hearing": {
        "arc_id": "education_slipping",
        "duration_months": 3,
        "severity": 2,
        "note": "Academic pressure has escalated into a real probation risk.",
    },
    "academic_funding_review": {
        "arc_id": "education_slipping",
        "duration_months": 2,
        "severity": 3,
        "note": "Funding pressure is compounding the school slide.",
    },
    "rent_increase": {
        "arc_id": "lease_pressure",
        "duration_months": 2,
        "severity": 1,
        "note": "Rent pressure is starting to tighten the housing lane.",
    },
    "lease_default_warning": {
        "arc_id": "lease_pressure",
        "duration_months": 4,
        "severity": 2,
        "note": "Housing instability is now an active lease problem, not just a tight month.",
    },
    "lease_enforcement_notice": {
        "arc_id": "lease_pressure",
        "duration_months": 4,
        "severity": 3,
        "note": "Lease pressure has escalated into enforcement risk.",
    },
    "overtime_attrition_warning": {
        "arc_id": "burnout_risk",
        "duration_months": 3,
        "severity": 2,
        "note": "The recovery lane is cracking under sustained work pressure.",
    },
    "burnout_month": {
        "arc_id": "burnout_risk",
        "duration_months": 3,
        "severity": 3,
        "note": "Burnout is now a live collapse risk, not just a bad month.",
    },
    "promotion_window": {
        "arc_id": "promotion_window_open",
        "duration_months": 3,
        "severity": 1,
        "note": "A real advancement opening is live for the next few months.",
    },
}

_CHOICE_RULES = {
    ("beater_cascade_choice", "eat_the_upgrade_hit"): {
        "action": "resolve",
        "arc_id": "transport_unstable",
    },
    ("beater_total_failure", "emergency_patch_transport"): {
        "action": "refresh",
        "arc_id": "transport_unstable",
        "duration_months": 2,
        "severity_delta": 0,
        "note": "You kept the commute alive, but transport is still shaping the run.",
    },
    ("beater_total_failure", "miss_shift_block"): {
        "action": "refresh",
        "arc_id": "transport_unstable",
        "duration_months": 3,
        "severity_delta": 1,
        "note": "Missed shifts turned transport instability into a direct work scar.",
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
    ("overtime_exam_collision", "protect_grades"): {
        "action": "refresh",
        "arc_id": "education_slipping",
        "duration_months": 1,
        "severity_delta": -1,
        "note": "You protected the lane, but the school slide still needs attention.",
    },
    ("overtime_exam_collision", "protect_paycheck"): {
        "action": "refresh",
        "arc_id": "education_slipping",
        "duration_months": 2,
        "severity_delta": 1,
        "note": "Cash won the month, and the school slide got worse.",
    },
    ("exam_probation_hearing", "cut_hours_and_recover_standing"): {
        "action": "refresh",
        "arc_id": "education_slipping",
        "duration_months": 1,
        "severity_delta": -1,
        "note": "Recovery work is slowing the slide, but the lane is still fragile.",
    },
    ("exam_probation_hearing", "push_through_probation"): {
        "action": "refresh",
        "arc_id": "education_slipping",
        "duration_months": 2,
        "severity_delta": 1,
        "note": "Pushing through is deepening the academic slide.",
    },
    ("academic_funding_review", "accept_study_contract"): {
        "action": "resolve",
        "arc_id": "education_slipping",
    },
    ("lease_enforcement_notice", "pay_to_hold_lease"): {
        "action": "refresh",
        "arc_id": "lease_pressure",
        "duration_months": 1,
        "severity_delta": -1,
        "note": "You held the lease, but housing pressure is still active.",
    },
    ("lease_enforcement_notice", "plan_fast_downgrade"): {
        "action": "resolve",
        "arc_id": "lease_pressure",
    },
    ("overtime_attrition_warning", "rebalance_workload"): {
        "action": "refresh",
        "arc_id": "burnout_risk",
        "duration_months": 1,
        "severity_delta": -1,
        "note": "You eased the load, but the recovery lane still needs protection.",
    },
    ("overtime_attrition_warning", "keep_forcing_hours"): {
        "action": "refresh",
        "arc_id": "burnout_risk",
        "duration_months": 2,
        "severity_delta": 1,
        "note": "Forcing hours is turning burnout risk into the shape of the run.",
    },
    ("burnout_month", "take_real_recovery"): {
        "action": "refresh",
        "arc_id": "burnout_risk",
        "duration_months": 1,
        "severity_delta": -2,
        "note": "You took the hit up front and finally gave recovery room to work.",
    },
    ("burnout_month", "mask_and_push"): {
        "action": "refresh",
        "arc_id": "burnout_risk",
        "duration_months": 2,
        "severity_delta": 1,
        "note": "You pushed through the crash and deepened the burnout scar.",
    },
    ("promotion_window", "push_for_scope"): {
        "action": "refresh",
        "arc_id": "promotion_window_open",
        "duration_months": 2,
        "severity_delta": 1,
        "note": "You pushed into the opening and raised both the upside and the pressure.",
    },
    ("promotion_window", "bank_consistency"): {
        "action": "refresh",
        "arc_id": "promotion_window_open",
        "duration_months": 2,
        "severity_delta": 0,
        "note": "You kept the opening alive through steady credibility instead of raw stretch.",
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
        severity_bonus = 0.14 * transport_arc.severity
        if event_id == "missed_shift_after_breakdown":
            multiplier *= 1.35 + severity_bonus
        elif event_id == "beater_cascade_choice":
            multiplier *= 1.22 + severity_bonus
        elif event_id == "beater_total_failure":
            multiplier *= 1.6 + severity_bonus
        elif event_id == "used_car_window":
            multiplier *= 1.12 + (0.09 * transport_arc.severity)
    credit_arc = get_active_status_arc(state, "credit_squeeze")
    if credit_arc is not None:
        severity_bonus = 0.12 * credit_arc.severity
        if event_id == "collections_warning":
            multiplier *= 1.22 + severity_bonus
        elif event_id == "credit_limit_review":
            multiplier *= 1.28 + severity_bonus
        elif event_id == "credit_rebuild_window":
            multiplier *= 1.12 + (0.07 * credit_arc.severity)
        elif event_id == "refinance_window":
            multiplier *= 1.14 + (0.06 * credit_arc.severity)
        elif event_id == "debt_fee_stack":
            multiplier *= 1.22 + (0.09 * credit_arc.severity)
    education_arc = get_active_status_arc(state, "education_slipping")
    if education_arc is not None:
        severity_bonus = 0.11 * education_arc.severity
        if event_id == "exam_probation_hearing":
            multiplier *= 1.28 + severity_bonus
        elif event_id == "academic_funding_review":
            multiplier *= 1.24 + severity_bonus
        elif event_id == "overtime_exam_collision":
            multiplier *= 1.14 + (0.08 * education_arc.severity)
    lease_arc = get_active_status_arc(state, "lease_pressure")
    if lease_arc is not None:
        severity_bonus = 0.11 * lease_arc.severity
        if event_id == "lease_default_warning":
            multiplier *= 1.24 + severity_bonus
        elif event_id == "lease_enforcement_notice":
            multiplier *= 1.32 + severity_bonus
        elif event_id == "rent_increase":
            multiplier *= 1.14 + (0.08 * lease_arc.severity)
    burnout_arc = get_active_status_arc(state, "burnout_risk")
    if burnout_arc is not None:
        severity_bonus = 0.11 * burnout_arc.severity
        if event_id == "burnout_month":
            multiplier *= 1.3 + severity_bonus
        elif event_id == "overtime_attrition_warning":
            multiplier *= 1.18 + (0.08 * burnout_arc.severity)
    promotion_arc = get_active_status_arc(state, "promotion_window_open")
    if promotion_arc is not None:
        severity_bonus = 0.08 * promotion_arc.severity
        if event_id == "promotion_window":
            multiplier *= 1.18 + severity_bonus
            if state.pending_promotion_branch_track_id == state.player.career.track_id:
                multiplier *= 1.18
        elif event_id in {
            "retail_leadership_offer",
            "sales_territory_offer",
            "dispatch_lead_offer",
            "equipment_specialist_offer",
            "warehouse_foreman_offer",
            "healthcare_shift_lead_offer",
            "clienteling_key_account_offer",
            "trades_crew_lead_offer",
            "retail_crisis_lead_backfill_offer",
        }:
            multiplier *= 1.14 + severity_bonus
    return multiplier
