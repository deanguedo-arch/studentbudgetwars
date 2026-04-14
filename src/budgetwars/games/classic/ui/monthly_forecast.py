from __future__ import annotations

from budgetwars.engine.scoring import credit_progress_summary, credit_tier_label, dominant_pressure_family

from .choice_previews import _money
from .diagnostics import (
    _active_status_arc_vms,
    _best_recovery_route,
    _blocked_door_lines,
    _build_crisis_warnings,
    _build_month_outlook_lines,
    _run_progress_fraction,
    _run_progress_text,
)
from .view_builders import (
    _current_focus_description,
    _current_focus_name,
    _format_persistent_commitments,
    _resolve_context,
)
from .view_models import MonthlyForecastVM


def build_monthly_forecast_vm(source, bundle=None) -> MonthlyForecastVM:
    controller = _resolve_context(source, bundle)
    state = controller.state
    player = state.player
    focus_name = _current_focus_name(controller)
    focus_description = _current_focus_description(controller)
    warnings = _build_crisis_warnings(state, controller.bundle)
    city = next(item for item in controller.bundle.cities if item.id == player.current_city_id)
    credit_tier = credit_tier_label(player.credit_score)
    credit_progress_label, credit_progress_detail, _ = credit_progress_summary(player.credit_score)
    situation_family = dominant_pressure_family(state)
    blocked_doors = _blocked_door_lines(state, controller.bundle)
    recovery_route = _best_recovery_route(state, controller.bundle)
    active_status_arcs = _active_status_arc_vms(state, controller.bundle)
    main_threat = (
        active_status_arcs[0].summary
        if active_status_arcs
        else (warnings[0] if warnings else (city.pressure_text or "No major threat is pressing right now."))
    )
    best_opportunity = city.opportunity_text
    expected_swing = f"Projected monthly swing {_money(player.monthly_surplus)} before pressure"
    recent_summary = list(state.recent_summary[:3])
    driver_notes = list(state.month_driver_notes[:5])
    if not recent_summary:
        recent_summary = _build_month_outlook_lines(state, controller.bundle)[-2:]
    progress_label, progress_detail = _run_progress_text(state)
    commitments = _format_persistent_commitments(player.persistent_tags)
    return MonthlyForecastVM(
        monthly_focus=focus_description,
        main_threat=main_threat,
        best_opportunity=best_opportunity,
        chosen_focus=focus_name,
        expected_swing=expected_swing,
        situation_family=situation_family,
        credit_status=f"{player.credit_score} {credit_tier} | {credit_progress_label}: {credit_progress_detail}",
        progress_label=progress_label,
        progress_detail=progress_detail,
        progress_fraction=_run_progress_fraction(state),
        persistent_commitments=commitments,
        active_status_arcs=active_status_arcs,
        recovery_route=recovery_route,
        blocked_doors=blocked_doors,
        driver_notes=driver_notes,
        recent_summary=recent_summary,
    )


def build_monthly_forecast(source, bundle=None) -> MonthlyForecastVM:
    return build_monthly_forecast_vm(source, bundle)
