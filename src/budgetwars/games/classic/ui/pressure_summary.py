from __future__ import annotations

from budgetwars.engine.scoring import (
    build_live_score_snapshot,
    credit_progress_summary,
    credit_tier_label,
    dominant_pressure_family,
)
from budgetwars.models import LiveScoreSnapshot

from .choice_previews import _money
from .diagnostics import (
    _active_status_arc_vms,
    _best_breakdown_category,
    _best_recovery_route,
    _blocked_door_lines,
    _build_crisis_warnings,
    _diagnosis_for_family,
    _pending_decision_lines,
    _pressure_map_lines,
    _score_progress_fraction,
    _score_progress_text,
    _status_arc_diagnosis,
)
from .view_builders import _format_persistent_commitments, _resolve_context
from .view_models import PressureMetricVM, PressureSummaryVM, ScoreDeltaVM


def build_pressure_summary_vm(source, bundle=None, snapshot: LiveScoreSnapshot | None = None) -> PressureSummaryVM:
    controller = _resolve_context(source, bundle)
    state = controller.state
    player = state.player
    snapshot = snapshot or build_live_score_snapshot(controller.bundle, state)
    credit_tier = credit_tier_label(player.credit_score)
    credit_progress_label, credit_progress_detail, credit_progress_fraction = credit_progress_summary(player.credit_score)
    active_modifiers = [
        f"{modifier.label} ({modifier.remaining_months})"
        for modifier in state.active_modifiers
    ]
    primary_metrics = [
        PressureMetricVM("Cash", _money(player.cash), tone="positive" if player.cash >= 0 else "negative"),
        PressureMetricVM("Savings", _money(player.savings), tone="positive"),
        PressureMetricVM("Debt", _money(player.debt), tone="negative" if player.debt > 0 else "neutral"),
    ]
    secondary_metrics = [
        PressureMetricVM("Income", _money(player.monthly_income), tone="positive"),
        PressureMetricVM("Expenses", _money(player.monthly_expenses), tone="negative"),
        PressureMetricVM("Monthly Swing", _money(player.monthly_surplus), tone="positive" if player.monthly_surplus >= 0 else "negative"),
        PressureMetricVM("Stress", f"{player.stress}/{state.max_stress}", tone="negative" if player.stress >= state.max_stress * 0.75 else "neutral"),
        PressureMetricVM("Energy", f"{player.energy}/{state.max_energy}", tone="negative" if player.energy <= 30 else "neutral"),
        PressureMetricVM("Life", f"{player.life_satisfaction}/{state.max_life_satisfaction}"),
        PressureMetricVM("Family", f"{player.family_support}/{state.max_family_support}"),
        PressureMetricVM("Social", f"{player.social_stability}/{state.max_social_stability}"),
        PressureMetricVM("Housing Stability", f"{player.housing.housing_stability}/100"),
        PressureMetricVM("Transport Reliability", f"{player.transport.reliability_score}/100"),
    ]
    progress_label, progress_detail = _score_progress_text(snapshot.projected_score)
    status_arc_diagnosis = _status_arc_diagnosis(state, controller.bundle)
    run_killer, fastest_fix = status_arc_diagnosis or _diagnosis_for_family(state)
    pressure_family = dominant_pressure_family(state)
    month_driver = (
        state.month_driver_notes[0]
        if state.month_driver_notes
        else _pressure_map_lines(state, controller.bundle)[0]
    )
    blocked_doors = _blocked_door_lines(state, controller.bundle)
    recovery_route = _best_recovery_route(state, controller.bundle)
    commitments = _format_persistent_commitments(player.persistent_tags)
    pending_decisions = _pending_decision_lines(state, controller.bundle)
    active_status_arcs = _active_status_arc_vms(state, controller.bundle)
    biggest_risk = active_status_arcs[0].name if active_status_arcs else snapshot.biggest_risk
    return PressureSummaryVM(
        projected_score=snapshot.projected_score,
        score_tier=snapshot.score_tier,
        biggest_risk=biggest_risk,
        credit_score=player.credit_score,
        credit_tier=credit_tier,
        credit_progress_label=credit_progress_label,
        credit_progress_detail=credit_progress_detail,
        credit_progress_fraction=credit_progress_fraction,
        progress_label=progress_label,
        progress_detail=progress_detail,
        progress_fraction=_score_progress_fraction(snapshot.projected_score),
        run_killer=run_killer,
        fastest_fix=fastest_fix,
        pressure_family=pressure_family,
        month_driver=month_driver,
        active_status_arcs=active_status_arcs,
        recovery_route=recovery_route,
        persistent_commitments=commitments,
        blocked_doors=blocked_doors,
        pending_fallout_count=len(state.pending_events),
        pending_decisions=pending_decisions,
        primary_metrics=primary_metrics,
        secondary_metrics=secondary_metrics,
        active_modifiers=active_modifiers,
        crisis_watch=_build_crisis_warnings(state, controller.bundle),
    )


def build_pressure_summary(source, bundle=None, snapshot: LiveScoreSnapshot | None = None) -> PressureSummaryVM:
    return build_pressure_summary_vm(source, bundle, snapshot=snapshot)


def build_score_delta_vm(prev_snapshot: LiveScoreSnapshot | None, snapshot: LiveScoreSnapshot) -> ScoreDeltaVM:
    if prev_snapshot is None:
        delta = 0.0
        prev_score = None
        prev_tier = None
    else:
        prev_score = prev_snapshot.projected_score
        prev_tier = prev_snapshot.score_tier
        delta = round(snapshot.projected_score - prev_snapshot.projected_score, 2)
    return ScoreDeltaVM(
        previous_score=prev_score,
        current_score=snapshot.projected_score,
        delta=delta,
        previous_tier=prev_tier,
        tier=snapshot.score_tier,
        strongest_category=_best_breakdown_category(snapshot.breakdown, reverse=True),
        weakest_category=_best_breakdown_category(snapshot.breakdown, reverse=False),
        diagnosis=snapshot.biggest_risk,
    )


def build_score_delta_summary(
    prev_snapshot: LiveScoreSnapshot | None,
    snapshot: LiveScoreSnapshot,
) -> ScoreDeltaVM:
    return build_score_delta_vm(prev_snapshot, snapshot)
