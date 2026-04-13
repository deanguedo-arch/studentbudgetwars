from __future__ import annotations

from budgetwars.engine.housing import can_switch_housing
from budgetwars.engine.scoring import credit_progress_summary, credit_tier_label, dominant_pressure_family
from budgetwars.engine.transport import can_switch_transport

from .choice_previews import _money
from .view_builders import _find_label
from .view_models import StatusArcVM


def _build_crisis_warnings(state, bundle) -> list[str]:
    player = state.player
    warnings: list[str] = []
    if player.credit_score < 580:
        warnings.append(f"Credit is limiting housing and transport options ({player.credit_score}).")
    elif player.credit_score < 670:
        warnings.append(f"Credit is still fair; some housing and transport doors stay narrow ({player.credit_score}).")
    if player.debt >= state.debt_game_over_threshold * bundle.config.crisis_warning_debt_ratio:
        warnings.append("Debt is getting close to collections.")
    if player.stress >= bundle.config.crisis_warning_stress:
        warnings.append("Stress is getting close to burnout territory.")
    if player.energy <= bundle.config.crisis_warning_energy:
        warnings.append("Energy is dangerously low.")
    if player.energy < 30:
        warnings.append("Energy is capping your income - overtime and gig hours are unreliable.")
    if player.housing.missed_payment_streak >= bundle.config.crisis_warning_housing_streak:
        warnings.append("Housing stability is wobbling.")
    if player.education.failure_streak >= max(1, state.academic_failure_streak_limit - 1):
        warnings.append("School pressure is close to a hard setback.")
    if player.housing.housing_stability <= 40:
        warnings.append("Housing stability is sliding and may cascade into stress.")
    if player.transport.reliability_score <= 45:
        warnings.append("Transport reliability is now threatening your work consistency.")
    if player.career.transition_penalty_months > 0:
        warnings.append("Career transition drag is still active.")
    if player.social_stability <= 35:
        warnings.append("Social isolation is dragging down recovery and performance.")
    if player.social_stability > 80:
        current_year = ((state.current_month - 1) // 12) + 1
        if player.last_social_lifeline_year < current_year:
            warnings.append("Your strong network can bail you out once this year if things go bad.")
    warnings.extend(_blocked_door_lines(state, bundle))
    if state.pending_events:
        warnings.append(f"Something is building - {len(state.pending_events)} consequence(s) pending.")
    if state.pending_promotion_branch_track_id:
        warnings.append("A promotion branch decision is pending.")
    return warnings


def _blocked_door_lines(state, bundle) -> list[str]:
    player = state.player
    blocked: list[str] = []
    if player.housing_id != "solo_rental":
        solo_allowed, solo_reason = can_switch_housing(bundle, state, "solo_rental")
        if not solo_allowed and ("credit" in solo_reason.lower() or "debt" in solo_reason.lower() or "lease" in solo_reason.lower()):
            blocked.append(f"Solo rental blocked: {solo_reason}")
    if player.transport_id != "financed_car":
        financed_allowed, financed_reason = can_switch_transport(bundle, state, "financed_car")
        if not financed_allowed and (
            "credit" in financed_reason.lower()
            or "debt" in financed_reason.lower()
            or "payment" in financed_reason.lower()
            or "cash" in financed_reason.lower()
        ):
            blocked.append(f"Financed car blocked: {financed_reason}")
    return blocked


def _best_recovery_route(state, bundle) -> str | None:
    player = state.player
    current_year = ((state.current_month - 1) // 12) + 1
    if (
        player.stress >= 78
        and player.social_stability >= 74
        and player.family_support >= 62
        and player.last_social_lifeline_year < current_year
    ):
        return "Best recovery route: your network can absorb one bad month if you stop forcing upside."
    if (
        player.credit_score >= 705
        and player.debt >= 2600
        and player.monthly_surplus >= 0
        and player.housing.missed_payment_streak == 0
    ):
        return "Best recovery route: strong credit can unlock debt relief if you keep the month clean."
    if (
        player.housing.housing_stability <= 34
        and player.current_city_id == "hometown_low_cost"
        and player.family_support >= bundle.config.minimum_parent_fallback_support + 8
        and player.housing.option_id != "parents"
    ):
        return "Best recovery route: move back home to stop the housing spiral before it compounds."
    if (
        player.housing.option_id in {"roommates", "solo_rental"}
        and player.housing.housing_stability <= 35
        and (player.housing.missed_payment_streak > 0 or player.monthly_surplus < 0)
        and ((player.savings + player.high_interest_savings) >= 900 or player.emergency_liquidation_count > 0)
        and player.wealth_strategy_id in {"cushion_first", "steady_builder"}
    ):
        return "Best recovery route: spend the cash buffer to stabilize housing instead of forcing growth."
    if player.stress >= 72:
        return "Best recovery route: run a recovery month and stop stacking pressure on a fragile turn."
    return None


def _active_status_arc_vms(state, bundle, *, limit: int = 3) -> list[StatusArcVM]:
    definitions = {arc.id: arc for arc in bundle.status_arcs}
    ranked = sorted(
        state.active_status_arcs,
        key=lambda arc: (
            definitions.get(arc.arc_id).ui_priority if definitions.get(arc.arc_id) is not None else 0,
            arc.severity,
            arc.remaining_months,
        ),
        reverse=True,
    )
    vms: list[StatusArcVM] = []
    for active in ranked[:limit]:
        definition = definitions.get(active.arc_id)
        if definition is None:
            continue
        vms.append(
            StatusArcVM(
                arc_id=active.arc_id,
                name=definition.name,
                summary=active.note or definition.summary,
                severity=active.severity,
                months_remaining=active.remaining_months,
                tone=definition.tone,
                resolution_hint=definition.resolution_hint,
                blocked_door_hints=list(definition.blocked_door_hints),
            )
        )
    return vms


def _pending_decision_lines(state, bundle) -> list[str]:
    lines: list[str] = []
    pending_event = state.pending_user_choice_event
    if pending_event is not None:
        lines.append(f"Situation choice pending: {pending_event.name}")
    elif state.pending_user_choice_event_id:
        event = next((item for item in bundle.events if item.id == state.pending_user_choice_event_id), None)
        label = event.name if event is not None else state.pending_user_choice_event_id.replace("_", " ").title()
        lines.append(f"Situation choice pending: {label}")
    if state.pending_promotion_branch_track_id:
        track = next((item for item in bundle.careers if item.id == state.pending_promotion_branch_track_id), None)
        lane = track.name if track is not None else state.pending_promotion_branch_track_id.replace("_", " ").title()
        lines.append(f"Promotion branch pending: {lane}")
    return lines


def _build_month_outlook_lines(state, bundle) -> list[str]:
    player = state.player
    city = next(item for item in bundle.cities if item.id == player.current_city_id)
    focus_name = _find_label(bundle.focus_actions, player.selected_focus_action_id, "Focus")
    credit_tier = credit_tier_label(player.credit_score)
    credit_progress_label, credit_progress_detail, _ = credit_progress_summary(player.credit_score)
    outlook = [
        f"{city.name}: {city.opportunity_text}",
        f"Pressure: {city.pressure_text}",
        f"Current lane: {player.career.track_id.replace('_', ' ').title()}.",
        f"Focus: {focus_name}.",
        f"Credit: {player.credit_score} ({credit_tier})",
        f"{credit_progress_label}: {credit_progress_detail}",
        f"Situation family: {dominant_pressure_family(state)}.",
    ]
    outlook.extend(_build_crisis_warnings(state, bundle))
    return outlook


def _best_breakdown_category(breakdown: dict[str, float], *, reverse: bool) -> str:
    labels = {
        "net_worth": "Net Worth",
        "monthly_surplus": "Cash Flow",
        "debt_ratio": "Debt",
        "career_tier": "Career",
        "credentials_education": "Education",
        "housing_stability": "Housing",
        "life_satisfaction": "Life",
        "stress_burnout": "Wellness",
    }
    key = max(breakdown, key=breakdown.get) if reverse else min(breakdown, key=breakdown.get)
    return labels.get(key, key.replace("_", " ").title())


def _score_progress_text(score: float) -> tuple[str, str]:
    if score < 40:
        return "Progress to Silver", f"{40 - score:.1f} points"
    if score < 60:
        return "Progress to Gold", f"{60 - score:.1f} points"
    if score < 80:
        return "Progress to Elite", f"{80 - score:.1f} points"
    return "Progress", "Top tier reached"


def _score_progress_fraction(score: float) -> float:
    if score < 40:
        return max(0.0, min(1.0, score / 40))
    if score < 60:
        return max(0.0, min(1.0, (score - 40) / 20))
    if score < 80:
        return max(0.0, min(1.0, (score - 60) / 20))
    return 1.0


def _diagnosis_for_family(state) -> tuple[str, str]:
    family = dominant_pressure_family(state)
    player = state.player
    if family == "Credit pressure":
        return ("Run killer: credit squeeze", "Fastest fix: stabilize monthly swing and stop debt growth.")
    if family == "Debt pressure":
        return ("Run killer: debt spiral", "Fastest fix: move to debt payoff and protect surplus.")
    if family == "Housing squeeze":
        return ("Run killer: unstable housing", "Fastest fix: reduce rent pressure or use fallback housing.")
    if family == "Transport friction":
        return ("Run killer: transport fragility", "Fastest fix: switch into reliability before pushing career.")
    if family == "Education pressure":
        return ("Run killer: school drag", "Fastest fix: lower education intensity until stress stabilizes.")
    if family == "Career turbulence":
        return ("Run killer: career turbulence", "Fastest fix: hold one lane and rebuild momentum.")
    if family == "Situation fallout":
        return ("Run killer: chained situations", "Fastest fix: clear active pressure cards before forcing upside.")
    if player.stress >= 75:
        return ("Run killer: burnout pressure", "Fastest fix: run recovery focus and protect sleep/energy.")
    return ("Run killer: none dominant", "Fastest fix: push your strongest lane while holding stability.")


def _status_arc_diagnosis(state, bundle) -> tuple[str, str] | None:
    active = _active_status_arc_vms(state, bundle, limit=1)
    if not active:
        return None
    top = active[0]
    run_killer = f"Run killer: {top.name.lower()}"
    if top.resolution_hint:
        fastest_fix = top.resolution_hint.replace("Best resolution: ", "Fastest fix: ")
    else:
        fastest_fix = "Fastest fix: stabilize the active scar before forcing upside."
    return run_killer, fastest_fix


def _run_progress_text(state) -> tuple[str, str]:
    current_month = state.current_month
    total_months = state.total_months
    months_complete = max(0, current_month - 1)
    run_pct = (months_complete / max(1, total_months)) * 100
    return (
        "Run progress",
        f"Month {current_month} of {total_months} | {run_pct:.0f}% complete",
    )


def _run_progress_fraction(state) -> float:
    return max(0.0, min(1.0, (max(0, state.current_month - 1)) / max(1, state.total_months)))


def _pressure_map_lines(state, bundle) -> list[str]:
    player = state.player
    focus_name = player.selected_focus_action_id.replace("_", " ")
    candidates: list[tuple[int, str]] = []

    work_pressure = player.stress + max(0, player.career.transition_penalty_months * 10)
    if player.selected_focus_action_id in {"overtime", "promotion_hunt"}:
        work_pressure += 10
    candidates.append((
        work_pressure,
        f"Work overload {'rising' if work_pressure >= 70 else 'stable'}: {focus_name.title()} and {player.career.track_id.replace('_', ' ')} are pushing recovery.",
    ))

    if player.housing.housing_stability <= 65 or player.housing.missed_payment_streak > 0:
        housing_pressure = (100 - player.housing.housing_stability) + (player.housing.missed_payment_streak * 15)
        candidates.append((
            housing_pressure,
            f"Housing squeeze {'rising' if housing_pressure >= 55 else 'stable'}: stability is {player.housing.housing_stability}/100 in {player.housing.option_id.replace('_', ' ')}.",
        ))

    if player.transport.reliability_score <= 70 or player.transport.breakdown_pressure > 0:
        transport_pressure = (100 - player.transport.reliability_score) + (player.transport.breakdown_pressure * 10)
        candidates.append((
            transport_pressure,
            f"Transport friction {'rising' if transport_pressure >= 55 else 'stable'}: reliability is {player.transport.reliability_score}/100 with {player.transport.option_id.replace('_', ' ')}.",
        ))

    debt_pressure = max(0, min(100, int(player.debt / 120))) + (20 if player.monthly_surplus < 0 else 0)
    if player.debt > 0 or player.credit_score < 670:
        candidates.append((
            debt_pressure,
            f"Debt anxiety {'rising' if debt_pressure >= 45 else 'stable'}: debt is {_money(player.debt)} and credit is {player.credit_score}.",
        ))

    if player.education.is_active or player.education.standing < 65:
        education_pressure = (100 - player.education.standing) + (player.education.failure_streak * 12)
        candidates.append((
            education_pressure,
            f"Education pressure {'rising' if education_pressure >= 50 else 'stable'}: standing is {player.education.standing}/100.",
        ))

    if player.social_stability <= 45 or player.family_support <= 40:
        support_pressure = (100 - player.social_stability) + max(0, 50 - player.family_support)
        candidates.append((
            support_pressure,
            f"Support strain {'rising' if support_pressure >= 55 else 'stable'}: family/social buffers are thin this month.",
        ))

    candidates.sort(key=lambda item: item[0], reverse=True)
    lines = [text for score, text in candidates if score > 0][:3]
    if not lines:
        return ["Pressure is fairly stable. Your monthly focus will drive most of the next swing."]
    return lines
