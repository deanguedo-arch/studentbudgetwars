from __future__ import annotations

from random import Random

from budgetwars.models import ContentBundle, EventChoice, EventDefinition, GameState, PendingEvent

from .effects import append_log, apply_stat_effects, clamp_player_state, create_modifier
from .lookups import get_city, get_housing_option, get_transport_option
from .status_arcs import (
    apply_choice_status_arc_resolution,
    apply_event_status_arc,
    get_active_status_arc,
    status_arc_event_weight_multiplier,
)

FAMILY_TO_MATRIX_KEY = {
    "Credit pressure": "credit_squeeze",
    "Housing squeeze": "housing_squeeze",
    "Transport friction": "transport_friction",
    "Education pressure": "education_drag",
    "Career turbulence": "career_breakthrough",
    "Family pressure": "support_buffer",
    "Wellbeing strain": "burnout_spiral",
    "Market shock": "opportunity_window",
    "General pressure": "debt_trap",
}

SEVERITY_EVENT_IDS = {
    "car_repair",
    "rent_increase",
    "job_layoff",
    "burnout_month",
    "credit_limit_review",
    "collections_warning",
    "security_deposit_shock",
    "financed_car_insurance_spike",
    "lease_default_warning",
    "lease_enforcement_notice",
    "beater_total_failure",
    "exam_probation_hearing",
    "academic_funding_review",
    "overtime_attrition_warning",
    "debt_fee_stack",
}


def event_family(event: EventDefinition) -> str:
    event_id = event.id.lower()
    event_name = event.name.lower()
    combined = f"{event_id} {event_name}"
    if any(token in combined for token in ("credit", "refinance", "bureau", "loan")):
        return "Credit pressure"
    if any(token in combined for token in ("rent", "roommate", "housing", "lease", "apartment")):
        return "Housing squeeze"
    if any(token in combined for token in ("car", "vehicle", "transport", "commute", "bike", "breakdown")):
        return "Transport friction"
    if any(token in combined for token in ("school", "education", "scholarship", "academic", "study")):
        return "Education pressure"
    if any(
        token in combined
        for token in (
            "layoff",
            "promotion",
            "sales",
            "job",
            "career",
            "gig",
            "work",
            "retail",
            "warehouse",
            "dispatch",
            "inventory",
            "commission",
            "client",
            "forklift",
            "equipment",
        )
    ):
        return "Career turbulence"
    if any(token in combined for token in ("family", "parent")):
        return "Family pressure"
    if any(token in combined for token in ("burnout", "stress", "energy", "health")):
        return "Wellbeing strain"
    if any(token in combined for token in ("market", "regime", "economic", "recession")):
        return "Market shock"
    return "General pressure"


def _credit_band_id(credit_score: int) -> str:
    if credit_score < 580:
        return "fragile"
    if credit_score < 670:
        return "fair"
    if credit_score < 740:
        return "strong"
    return "prime"


def _uses_vehicle(transport_id: str) -> bool:
    return transport_id in {"beater_car", "financed_car", "reliable_used_car", "luxury_financed_car"}


def _consequence_layers(bundle: ContentBundle, state: GameState) -> list:
    matrix = bundle.consequence_matrix
    player = state.player
    layers = []
    for entries, key in (
        (matrix.budget_stances, player.budget_stance_id),
        (matrix.wealth_strategies, player.wealth_strategy_id),
        (matrix.housing_options, player.housing_id),
        (matrix.transport_options, player.transport_id),
        (matrix.education_programs, player.education.program_id),
        (matrix.focus_actions, player.selected_focus_action_id),
        (matrix.career_tracks, player.career.track_id),
        (matrix.credit_bands, _credit_band_id(player.credit_score)),
    ):
        layer = entries.get(key)
        if layer is not None:
            layers.append(layer)
    return layers


def _is_blocked_by_matrix(bundle: ContentBundle, state: GameState, event_id: str) -> bool:
    return any(event_id in layer.blockers for layer in _consequence_layers(bundle, state))


def _matrix_weight_multiplier(bundle: ContentBundle, state: GameState, event: EventDefinition) -> float:
    multiplier = 1.0
    unlocked = False
    for layer in _consequence_layers(bundle, state):
        event_scale = layer.event_weights.get(event.id)
        if event_scale is not None:
            multiplier *= max(0.05, float(event_scale))
        if event.id in layer.unlocks:
            unlocked = True
    if unlocked:
        multiplier *= 1.2
    pressure_key = FAMILY_TO_MATRIX_KEY.get(event_family(event))
    if pressure_key:
        pressure_shift = sum(float(layer.pressure_families.get(pressure_key, 0.0)) for layer in _consequence_layers(bundle, state))
        multiplier *= max(0.35, 1.0 + pressure_shift)
    return max(0.05, multiplier)


def _resilience_score(state: GameState) -> float:
    player = state.player
    liquid = player.cash + player.savings + player.high_interest_savings
    score = 0.0
    if liquid < 250:
        score -= 0.9
    elif liquid < 900:
        score -= 0.45
    elif liquid > 3500:
        score += 0.4
    if player.debt >= 22000:
        score -= 0.8
    elif player.debt >= 9000:
        score -= 0.4
    elif player.debt <= 2500:
        score += 0.25
    if player.credit_score < 580:
        score -= 0.6
    elif player.credit_score >= 720:
        score += 0.35
    if player.housing.housing_stability < 45:
        score -= 0.5
    elif player.housing.housing_stability >= 72:
        score += 0.2
    if player.transport.reliability_score < 50:
        score -= 0.45
    elif player.transport.reliability_score >= 82:
        score += 0.2
    if player.stress >= 78:
        score -= 0.55
    elif player.stress <= 38:
        score += 0.2
    if player.energy <= 28:
        score -= 0.5
    elif player.energy >= 72:
        score += 0.2
    if player.family_support <= 28:
        score -= 0.25
    elif player.family_support >= 68:
        score += 0.15
    if player.social_stability <= 32:
        score -= 0.25
    elif player.social_stability >= 65:
        score += 0.15
    return score


def _branch_weight_multiplier(state: GameState, event: EventDefinition) -> float:
    player = state.player
    branch_id = player.career.branch_id
    if not branch_id:
        return 1.0

    multiplier = 1.0
    if event.eligible_branch_ids and branch_id in event.eligible_branch_ids:
        multiplier *= 1.25

    if player.career.track_id == "retail_service":
        if branch_id == "retail_management_track":
            if event.id in {
                "retail_inventory_crunch",
                "management_overload_wave",
                "retail_leadership_offer",
                "retail_crisis_lead_backfill_offer",
                "retail_sustainable_ops_dividend",
            }:
                multiplier *= 1.35
            if event.id in {"burnout_month", "overtime_attrition_warning"} and player.stress >= 64:
                multiplier *= 1.2
            if event.id == "job_layoff" and player.stress >= 74:
                multiplier *= 1.15
        elif branch_id == "retail_sales_track":
            if event.id in {"sales_whale_month", "sales_territory_offer"}:
                multiplier *= 1.35
            if event.id == "sales_hot_streak" and player.social_stability >= 66:
                multiplier *= 1.35
            if event.id == "sales_cold_streak" and player.social_stability < 58:
                multiplier *= 1.35
        elif branch_id == "retail_clienteling_track":
            if event.id in {"client_book_referral", "clienteling_key_account_offer"} and player.social_stability >= 64:
                multiplier *= 1.4
            if event.id == "client_book_attrition_risk" and (player.social_stability <= 58 or player.stress >= 68):
                multiplier *= 1.35
            if event.id == "job_layoff" and player.social_stability >= 68 and player.housing.housing_stability >= 55:
                multiplier *= 0.85

    if player.career.track_id == "warehouse_logistics":
        if branch_id == "warehouse_ops_track":
            if event.id in {"dock_bottleneck", "warehouse_foreman_offer"}:
                multiplier *= 1.35
            if event.id == "warehouse_safety_crunch" and (player.energy < 42 or player.transport.reliability_score < 66):
                multiplier *= 1.4
        elif branch_id == "warehouse_dispatch_track":
            if event.id in {
                "dispatch_route_rewrite",
                "dispatch_fire_drill",
                "dispatch_process_upgrade",
                "dispatch_lead_offer",
                "dispatch_escalation_penalty_cycle",
                "dispatch_resilience_compound",
            }:
                multiplier *= 1.35
            if event.id == "dispatch_process_upgrade" and player.social_stability >= 56 and player.transport.reliability_score >= 68:
                multiplier *= 1.15
        elif branch_id == "warehouse_equipment_track":
            if event.id in {"equipment_cert_window", "equipment_shift_contract", "equipment_specialist_offer"}:
                multiplier *= 1.35
            if event.id == "equipment_safety_recall" and (player.transport.reliability_score < 66 or player.stress >= 70):
                multiplier *= 1.35

    return max(0.35, multiplier)


def event_severity_multiplier(bundle: ContentBundle, state: GameState, event: EventDefinition) -> float:
    if event.id not in SEVERITY_EVENT_IDS:
        return 1.0
    multiplier = 1.0
    for layer in _consequence_layers(bundle, state):
        severity_scale = layer.event_severity.get(event.id)
        if severity_scale is not None:
            multiplier *= max(0.4, float(severity_scale))
    resilience = _resilience_score(state)
    multiplier += (-resilience * 0.12)
    family_key = FAMILY_TO_MATRIX_KEY.get(event_family(event))
    if family_key:
        pressure_shift = sum(float(layer.pressure_families.get(family_key, 0.0)) for layer in _consequence_layers(bundle, state))
        multiplier += pressure_shift * 0.25
    if event.id == "car_repair" and state.player.transport.reliability_score < 55:
        multiplier += 0.18
    if event.id == "rent_increase" and state.player.housing.housing_stability < 45:
        multiplier += 0.16
    if event.id == "job_layoff" and state.player.career.recent_performance_tag == "downtrend":
        multiplier += 0.14
    if event.id == "burnout_month" and state.player.selected_focus_action_id in {"overtime", "promotion_hunt"}:
        multiplier += 0.12
    if event.id == "credit_limit_review" and state.player.credit_score < 580:
        multiplier += 0.16
    if event.id == "collections_warning" and state.player.credit_score < 600:
        multiplier += 0.2
    if event.id == "security_deposit_shock" and state.player.credit_score < 620:
        multiplier += 0.16
    if event.id == "financed_car_insurance_spike" and state.player.credit_score < 640:
        multiplier += 0.12
    if event.id in {"credit_limit_review", "collections_warning", "security_deposit_shock", "financed_car_insurance_spike"}:
        if state.player.credit_missed_obligation_streak >= 1:
            multiplier += min(0.24, state.player.credit_missed_obligation_streak * 0.06)
        if state.player.credit_utilization_pressure >= 70:
            multiplier += 0.12
    return max(0.7, min(1.8, multiplier))


def _scaled_effects(effects: dict[str, float], multiplier: float) -> dict[str, float]:
    if multiplier == 1.0:
        return dict(effects)
    return {key: int(round(value * multiplier)) for key, value in effects.items()}


def _event_is_eligible(bundle: ContentBundle, state: GameState, event: EventDefinition) -> bool:
    player = state.player
    active_modifier_ids = {modifier.id for modifier in state.active_modifiers}
    if state.current_month < event.min_month:
        return False
    if event.eligible_city_ids and player.current_city_id not in event.eligible_city_ids:
        return False
    if event.eligible_housing_ids and player.housing_id not in event.eligible_housing_ids:
        return False
    if event.eligible_transport_ids and player.transport_id not in event.eligible_transport_ids:
        return False
    if event.eligible_career_ids and player.career.track_id not in event.eligible_career_ids:
        return False
    if event.eligible_branch_ids and player.career.branch_id not in event.eligible_branch_ids:
        return False
    if event.eligible_education_ids and player.education.program_id not in event.eligible_education_ids:
        return False
    if event.eligible_opening_path_ids and player.opening_path_id not in event.eligible_opening_path_ids:
        return False
    if event.eligible_modifier_ids and not set(event.eligible_modifier_ids).issubset(active_modifier_ids):
        if event.id == "academic_funding_review":
            education_arc = get_active_status_arc(state, "education_slipping")
            if education_arc is None or education_arc.severity < 2:
                return False
        elif event.id == "lease_enforcement_notice":
            lease_arc = get_active_status_arc(state, "lease_pressure")
            if lease_arc is None or lease_arc.severity < 2:
                return False
        else:
            return False
    if event.eligible_persistent_tags and not set(event.eligible_persistent_tags).issubset(set(player.persistent_tags)):
        return False
    if event.eligible_wealth_strategy_ids and player.wealth_strategy_id not in event.eligible_wealth_strategy_ids:
        return False
    if event.minimum_stress is not None and player.stress < event.minimum_stress:
        return False
    if event.minimum_debt is not None and player.debt < event.minimum_debt:
        return False
    if event.minimum_family_support is not None and player.family_support < event.minimum_family_support:
        return False
    if event.maximum_family_support is not None and player.family_support > event.maximum_family_support:
        return False
    if event.minimum_social_stability is not None and player.social_stability < event.minimum_social_stability:
        return False
    if event.maximum_social_stability is not None and player.social_stability > event.maximum_social_stability:
        return False
    if event.maximum_transport_reliability is not None and player.transport.reliability_score > event.maximum_transport_reliability:
        return False
    if event.maximum_housing_stability is not None and player.housing.housing_stability > event.maximum_housing_stability:
        return False
    if event.maximum_life_satisfaction is not None and player.life_satisfaction > event.maximum_life_satisfaction:
        return False
    if event.minimum_credit_score is not None and player.credit_score < event.minimum_credit_score:
        return False
    if event.maximum_credit_score is not None and player.credit_score > event.maximum_credit_score:
        return False
    if event.id == "credit_rebuild_window":
        if player.monthly_surplus < 150:
            return False
        if player.debt > 5000:
            return False
        if player.housing.missed_payment_streak > 0:
            return False
        if (player.cash + player.savings) < 1200:
            return False
        if player.credit_missed_obligation_streak > 0:
            return False
        if player.credit_utilization_pressure >= 78:
            return False
    if event.id == "collections_warning":
        if player.monthly_surplus > -50:
            return False
    if event.id == "beater_cascade_choice":
        if player.transport.option_id != "beater_car":
            return False
        if player.transport.reliability_score > 55:
            return False
    if event.id == "overtime_exam_collision":
        if not player.education.is_active:
            return False
        if player.education.intensity_level == "intensive":
            pass
        elif player.selected_focus_action_id not in {"overtime", "study_push", "promotion_hunt"}:
            return False
    if event.id == "prime_refi_bridge":
        if player.monthly_surplus > 80:
            return False
        if player.debt < 4500:
            return False
        if player.credit_score < 740:
            return False
        if player.credit_missed_obligation_streak >= 2:
            return False
    if event.id == "refinance_window":
        if player.credit_missed_obligation_streak >= 2:
            return False
    if event.id == "family_stability_surge":
        if player.monthly_surplus < 140:
            return False
        if player.housing.missed_payment_streak > 0:
            return False
    if event.id == "emergency_fund_redeployment":
        if (player.cash + player.savings + player.high_interest_savings) < 1600:
            return False
        if player.monthly_surplus < 120:
            return False
    if event.id == "lease_default_warning":
        if player.monthly_surplus > -120:
            return False
        if (player.cash + player.savings) > 650:
            return False
    if event.id == "lease_enforcement_notice":
        if player.housing.option_id != "solo_rental":
            return False
        if player.monthly_surplus > -80:
            return False
    if event.id == "debt_fee_stack":
        if player.monthly_surplus > -40:
            return False
    if event.id == "beater_total_failure":
        if player.transport.option_id != "beater_car":
            return False
        if player.transport.reliability_score > 42:
            return False
        if player.monthly_surplus > 90:
            return False
    if event.id == "route_reliability_bonus":
        if player.transport.reliability_score < 72:
            return False
        if player.monthly_surplus < 0:
            return False
    if event.id == "exam_probation_hearing":
        if not player.education.is_active:
            return False
        if player.education.program_id not in {"full_time_university", "part_time_college"}:
            return False
        if player.selected_focus_action_id not in {"overtime", "study_push", "promotion_hunt"}:
            return False
        if player.stress < 62 and player.energy > 45:
            return False
    if event.id == "academic_funding_review":
        if not player.education.is_active:
            return False
        if player.education.program_id not in {"full_time_university", "part_time_college"}:
            return False
    if event.id == "overtime_attrition_warning":
        if player.selected_focus_action_id not in {"overtime", "promotion_hunt"}:
            return False
        if player.stress < 68:
            return False
    if event.id == "family_support_bridge":
        if (player.cash + player.savings) > 1300:
            return False
        if player.monthly_surplus > 60:
            return False
    if event.id == "market_margin_call":
        if player.monthly_surplus > -40:
            return False
        if (player.cash + player.savings) > 900:
            return False
    if event.id == "debt_paydown_tightrope":
        if player.monthly_surplus < 50:
            return False
        if (player.cash + player.savings) > 700:
            return False
    if event.id == "cash_drag_regret":
        if player.monthly_surplus < 180:
            return False
        if (player.cash + player.savings) < 1800:
            return False
    if event.id == "steady_compound_window":
        if player.monthly_surplus < 120:
            return False
        if player.debt > 7800:
            return False
        if (player.cash + player.savings) < 1200:
            return False
        if player.credit_score < 650:
            return False
    if event.id == "dry_powder_window":
        if (player.cash + player.savings + player.high_interest_savings) < 900:
            return False
    if event.eligible_market_regime_ids and state.current_market_regime_id not in event.eligible_market_regime_ids:
        return False
    if event.id in {"car_repair", "beater_breakdown", "missed_shift_after_breakdown", "used_car_window"} and not _uses_vehicle(player.transport_id):
        return False
    if _is_blocked_by_matrix(bundle, state, event.id):
        return False
    return True


def eligible_events(bundle: ContentBundle, state: GameState) -> list[EventDefinition]:
    return [event for event in bundle.events if _event_is_eligible(bundle, state, event)]


def event_weight(bundle: ContentBundle, state: GameState, event: EventDefinition) -> float:
    weight = float(event.weight)
    housing = get_housing_option(bundle, state.player.housing_id)
    transport = get_transport_option(bundle, state.player.transport_id)
    city = get_city(bundle, state.player.current_city_id)
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)
    transport_arc = get_active_status_arc(state, "transport_unstable")

    if event.id == "roommate_conflict":
        weight *= max(0.05, housing.roommate_event_weight)
    if event.id == "roommate_missed_bill":
        weight *= max(0.05, housing.roommate_event_weight)
    if event.id == "roommate_moves_out":
        weight *= max(0.05, housing.roommate_event_weight * 0.9)
    if event.id == "car_repair":
        weight *= max(0.05, transport.repair_event_weight)
    if event.id == "beater_breakdown":
        weight *= max(0.05, transport.repair_event_weight * 1.15)
    if event.id == "missed_shift_after_breakdown":
        weight *= max(0.05, transport.repair_event_weight * 0.8)
    if event.id == "used_car_window" and transport.access_level >= 3 and (
        transport_arc is None or transport_arc.severity < 2
    ):
        weight *= 0.2
    if event.id == "used_car_window" and state.player.credit_score >= 700:
        weight *= 0.45
    if event.id == "promotion_window":
        track = next(track for track in bundle.careers if track.id == state.player.career.track_id)
        weight *= track.promotion_weight
    if event.id == "job_layoff":
        track = next(track for track in bundle.careers if track.id == state.player.career.track_id)
        weight *= track.layoff_weight
    if event.id == "scholarship_relief":
        if not state.player.education.is_active:
            weight *= 0.2
        elif state.player.education.college_gpa >= 3.2:
            weight *= 1.5
        elif state.player.education.college_gpa < 2.3:
            weight *= 0.65
    if event.id == "rent_increase" and housing.id == "solo_rental":
        weight *= 1.2
    if event.id == "family_emergency" and city.id == "hometown_low_cost":
        weight *= 1.15
    if event.id == "family_emergency" and state.player.family_support <= 35:
        weight *= 1.25
    if event.id == "parent_bailout":
        weight *= 1.1 if state.player.family_support >= 70 else 0.9
    if event.id == "parent_boundary":
        weight *= 1.2 if state.player.career.recent_performance_tag == "downtrend" else 1.0
    if event.id == "burnout_month" and state.player.selected_focus_action_id in {"overtime", "promotion_hunt"}:
        weight *= 1.15
    if event.id == "burnout_month" and state.player.career.transition_penalty_months > 0:
        weight *= 1.2
    if event.id == "side_hustle_window" and state.player.selected_focus_action_id == "side_gig":
        weight *= 1.35
    if event.id == "job_layoff" and state.player.career.recent_performance_tag == "downtrend":
        weight *= 1.2
    if event.id == "job_layoff" and state.player.career.recent_performance_tag == "uptrend":
        weight *= 0.85
    if event.id == "rent_increase" and state.player.housing.housing_stability < 45:
        weight *= 1.15
    if event.id == "car_repair" and state.player.transport.reliability_score < 55:
        weight *= 1.35
    if event.id == "car_repair" and state.player.transport.option_id == "financed_car":
        weight *= 1.1
    if event.id == "used_car_window" and state.current_market_regime_id in {"weak", "correction"}:
        weight *= 1.2
    if event.id == "economic_downturn" and state.current_market_regime_id in {"weak", "correction"}:
        weight *= 1.25
    if event.id == "scholarship_relief" and state.player.education.education_momentum >= 60:
        weight *= 1.2
    if event.id == "sales_hot_streak" and state.player.career.recent_performance_tag == "uptrend":
        weight *= 1.3
    if event.id == "sales_cold_streak" and state.player.career.recent_performance_tag == "downtrend":
        weight *= 1.35
    if event.id == "financed_car_insurance_spike" and state.player.monthly_surplus < 0:
        weight *= 1.2
    if event.id == "credit_limit_review":
        if state.player.credit_score < 620:
            weight *= 1.7
        if state.player.debt >= 2000:
            weight *= 1.15
        if state.player.credit_missed_obligation_streak >= 1:
            weight *= min(1.45, 1.1 + (state.player.credit_missed_obligation_streak * 0.12))
        if state.player.credit_utilization_pressure >= 68:
            weight *= 1.2
    if event.id == "refinance_window":
        if state.player.credit_score >= 700:
            weight *= 1.8
        elif state.player.credit_score >= 670:
            weight *= 1.2
        else:
            weight *= 0.25
        if state.player.debt >= 2500:
            weight *= 1.15
        if state.player.credit_rebuild_streak >= 2:
            weight *= 1.2
        if state.player.credit_missed_obligation_streak >= 1:
            weight *= 0.6
    if event.id == "credit_rebuild_window":
        if state.player.monthly_surplus >= 250:
            weight *= 1.5
        if state.player.debt <= 4000:
            weight *= 1.25
        if state.player.housing.missed_payment_streak > 0:
            weight *= 0.2
        if state.player.credit_rebuild_streak >= 2:
            weight *= 1.35
        if state.player.credit_missed_obligation_streak > 0:
            weight *= 0.35
    if event.id == "beater_cascade_choice":
        if state.player.transport.option_id == "beater_car":
            weight *= 1.45
        if state.player.transport.reliability_score <= 45:
            weight *= 1.35
        if state.player.debt >= 7000:
            weight *= 1.2
        if state.player.cash + state.player.savings < 500:
            weight *= 1.15
    if event.id == "overtime_exam_collision":
        if state.player.education.is_active:
            weight *= 1.25
        if state.player.selected_focus_action_id in {"overtime", "study_push"}:
            weight *= 1.35
        if state.player.energy <= 45:
            weight *= 1.2
        if state.player.stress >= 65:
            weight *= 1.2
        if state.player.education.intensity_level == "intensive":
            weight *= 1.2
        if state.player.education.program_id == "none":
            weight *= 0.15
    if event.id == "collections_warning":
        if state.player.credit_score < 580:
            weight *= 1.45
        elif state.player.credit_score >= 700:
            weight *= 0.2
        if state.player.debt >= 9000:
            weight *= 1.35
        if state.player.monthly_surplus < 0:
            weight *= 1.3
        if state.player.cash + state.player.savings < 600:
            weight *= 1.2
        if state.player.credit_missed_obligation_streak >= 1:
            weight *= min(1.5, 1.15 + (state.player.credit_missed_obligation_streak * 0.1))
        if state.player.credit_utilization_pressure >= 70:
            weight *= 1.2
    if event.id == "prime_refi_bridge":
        if state.player.credit_score >= 760:
            weight *= 1.2
        if state.player.debt >= 7000:
            weight *= 1.25
        if state.player.monthly_surplus < 0:
            weight *= 1.25
        if state.player.cash + state.player.savings < 600:
            weight *= 1.2
        if state.player.credit_rebuild_streak >= 2:
            weight *= 1.15
        if state.player.credit_missed_obligation_streak >= 1:
            weight *= 0.75
    if event.id == "market_margin_call":
        if state.player.monthly_surplus < -120:
            weight *= 1.2
        if state.player.cash + state.player.savings < 300:
            weight *= 1.25
        if state.player.debt >= 10000:
            weight *= 1.2
        if state.player.index_fund + state.player.aggressive_growth_fund >= 4500:
            weight *= 1.2
    if event.id == "debt_paydown_tightrope":
        if state.player.debt >= 8500:
            weight *= 1.25
        if state.player.cash + state.player.savings < 300:
            weight *= 1.2
        if state.player.stress >= 60:
            weight *= 1.15
        if state.player.monthly_surplus >= 140:
            weight *= 1.1
    if event.id == "cash_drag_regret":
        if state.player.cash + state.player.savings >= 2400:
            weight *= 1.25
        if state.player.monthly_surplus >= 280:
            weight *= 1.2
    if event.id == "market_panic_window":
        if state.player.index_fund + state.player.aggressive_growth_fund >= 5000:
            weight *= 1.3
        if state.player.cash + state.player.savings < 600:
            weight *= 1.2
    if event.id == "dry_powder_window":
        if state.player.cash + state.player.savings + state.player.high_interest_savings >= 1800:
            weight *= 1.25
        if state.player.monthly_surplus >= 120:
            weight *= 1.15
    if event.id == "steady_compound_window":
        if state.player.monthly_surplus >= 220:
            weight *= 1.3
        if state.player.debt <= 4500:
            weight *= 1.2
        if state.player.credit_score >= 700:
            weight *= 1.15
    if event.id == "family_stability_surge":
        if state.player.housing.option_id == "parents":
            weight *= 1.25
        if state.player.family_support >= 75:
            weight *= 1.2
        if state.player.monthly_surplus >= 220:
            weight *= 1.2
    if event.id == "lease_default_warning":
        if state.player.housing.option_id == "solo_rental":
            weight *= 1.35
        if state.player.monthly_surplus <= -180:
            weight *= 1.3
        if state.player.credit_score < 580:
            weight *= 1.25
        if state.player.credit_missed_obligation_streak >= 1:
            weight *= min(1.5, 1.15 + (state.player.credit_missed_obligation_streak * 0.1))
        if state.player.credit_utilization_pressure >= 68:
            weight *= 1.15
    if event.id == "beater_total_failure":
        if state.player.transport.option_id == "beater_car":
            weight *= 1.35
        if state.player.transport.reliability_score <= 38:
            weight *= 1.3
        if state.player.monthly_surplus < -50:
            weight *= 1.2
    if event.id == "exam_probation_hearing":
        if state.player.selected_focus_action_id in {"overtime", "study_push"}:
            weight *= 1.25
        if state.player.stress >= 70:
            weight *= 1.2
        if state.player.energy <= 42:
            weight *= 1.2
    if event.id == "overtime_attrition_warning":
        if state.player.selected_focus_action_id == "overtime":
            weight *= 1.3
        if state.player.stress >= 74:
            weight *= 1.2

    weight *= status_arc_event_weight_multiplier(state, event.id)
    weight *= _branch_weight_multiplier(state, event)
    weight *= _matrix_weight_multiplier(bundle, state, event)
    return max(0.05, weight * difficulty.event_weight_multiplier)


def pick_event(bundle: ContentBundle, state: GameState, rng: Random, excluded_ids: set[str] | None = None) -> EventDefinition | None:
    candidates = [event for event in eligible_events(bundle, state) if not excluded_ids or event.id not in excluded_ids]
    if not candidates:
        return None
    weights = [event_weight(bundle, state, event) for event in candidates]
    return rng.choices(candidates, weights=weights, k=1)[0]


def resolve_event(bundle: ContentBundle, state: GameState, event: EventDefinition) -> None:
    append_log(state, f"Situation family: {event_family(event)}")
    multiplier = event_severity_multiplier(bundle, state, event)
    apply_event_status_arc(bundle, state, event.id)
    if event.choices:
        state.pending_user_choice_event_id = event.id
        state.pending_user_choice_event = event.model_copy(deep=True)
        if multiplier != 1.0:
            for choice in state.pending_user_choice_event.choices:
                choice.stat_effects = _scaled_effects(choice.stat_effects, multiplier)
        append_log(state, event.log_entry or f"Choice pending: {event.name}")
        return
    apply_stat_effects(state, _scaled_effects(event.immediate_effects, multiplier))
    if event.modifier is not None:
        state.active_modifiers.append(create_modifier(event.modifier))
        append_log(state, f"Modifier gained: {event.modifier.label} ({event.modifier.duration_months} months)")
    if event.chained_event_id:
        state.pending_events.append(
            PendingEvent(
                event_id=event.chained_event_id,
                months_remaining=max(1, event.chained_delay_months),
                source_event_id=event.id,
            )
        )
        append_log(state, f"Something worse may follow from this ({event.chained_delay_months}mo)...")
    append_log(state, event.log_entry or event.name)


def resolve_event_choice(
    bundle: ContentBundle,
    state: GameState,
    event_id: str,
    choice_id: str,
) -> EventChoice:
    event = state.pending_user_choice_event
    if event is None or event.id != event_id:
        event = next((item for item in bundle.events if item.id == event_id), None)
    if event is None:
        raise ValueError(f"Unknown event '{event_id}'.")
    if not event.choices:
        raise ValueError(f"Event '{event_id}' does not have any choices.")
    if state.pending_user_choice_event_id not in {None, event_id}:
        raise ValueError("A different event choice is already pending.")
    choice = next((item for item in event.choices if item.id == choice_id), None)
    if choice is None:
        raise ValueError(f"Unknown choice '{choice_id}' for event '{event_id}'.")

    apply_stat_effects(state, choice.stat_effects)
    if event.modifier is not None:
        state.active_modifiers.append(create_modifier(event.modifier))
        append_log(state, f"Modifier gained: {event.modifier.label} ({event.modifier.duration_months} months)")
    if choice.modifier is not None:
        state.active_modifiers.append(create_modifier(choice.modifier))
        append_log(state, f"Modifier gained: {choice.modifier.label} ({choice.modifier.duration_months} months)")
    if choice.persistent_tag and choice.persistent_tag not in state.player.persistent_tags:
        state.player.persistent_tags.append(choice.persistent_tag)
        append_log(state, f"Career commitment set: {choice.persistent_tag.replace('_', ' ')}")
    apply_choice_status_arc_resolution(state, event.id, choice.id)
    _apply_structural_choice_followthrough(state, event.id, choice.id)
    if event.chained_event_id:
        state.pending_events.append(
            PendingEvent(
                event_id=event.chained_event_id,
                months_remaining=max(1, event.chained_delay_months),
                source_event_id=event.id,
            )
        )
        append_log(state, f"Something worse may follow from this ({event.chained_delay_months}mo)...")
    state.pending_user_choice_event_id = None
    state.pending_user_choice_event = None
    append_log(state, f"Choice made: {event.name} -> {choice.label}")
    if choice.description:
        append_log(state, choice.description)
    return choice


def _apply_structural_choice_followthrough(state: GameState, event_id: str, choice_id: str) -> None:
    player = state.player

    if (event_id, choice_id) == ("credit_limit_review", "tighten_up"):
        player.credit_utilization_pressure = max(0, player.credit_utilization_pressure - 8)
        player.credit_rebuild_streak = max(player.credit_rebuild_streak, 1)
        append_log(state, "Credit cleanup reduced utilization pressure and put your rebuild back on track.")
    elif (event_id, choice_id) == ("refinance_window", "refinance_now"):
        player.credit_utilization_pressure = max(0, player.credit_utilization_pressure - 10)
        player.credit_rebuild_streak = max(player.credit_rebuild_streak, 1)
        append_log(state, "Refinancing opened real breathing room in the credit file.")
    elif (event_id, choice_id) == ("reserve_deployment_window", "spend_buffer_now"):
        player.housing.missed_payment_streak = max(0, player.housing.missed_payment_streak - 1)
        player.housing.housing_stability = min(100, player.housing.housing_stability + 5)
        append_log(state, "Reserve deployment stabilized the lease lane instead of only buying time.")
    elif (event_id, choice_id) == ("burnout_month", "take_real_recovery"):
        state.burnout_streak = 0
        append_log(state, "Real recovery broke the burnout streak before it could compound again.")
    elif (event_id, choice_id) == ("exam_probation_hearing", "cut_hours_and_recover_standing"):
        player.education.standing = min(100, player.education.standing + 4)
        player.education.education_momentum = min(100, player.education.education_momentum + 6)
        append_log(state, "The probation recovery plan restored academic footing and momentum.")

    clamp_player_state(state)


def _tick_pending_events(bundle: ContentBundle, state: GameState) -> list[EventDefinition]:
    """Decrement pending event timers and force-trigger any that have matured."""
    triggered: list[EventDefinition] = []
    remaining: list[PendingEvent] = []
    for pending in state.pending_events:
        pending.months_remaining -= 1
        if pending.months_remaining <= 0:
            event_def = next(
                (e for e in bundle.events if e.id == pending.event_id), None
            )
            if event_def:
                resolve_event(bundle, state, event_def)
                triggered.append(event_def)
                append_log(state, f"A consequence of {pending.source_event_id.replace('_', ' ')} arrived.")
            # Drop it whether or not we found the definition
        else:
            remaining.append(pending)
    state.pending_events = remaining
    return triggered


def roll_month_events(bundle: ContentBundle, state: GameState, rng: Random) -> list[EventDefinition]:
    rolled: list[EventDefinition] = []
    excluded: set[str] = set()

    # Force-trigger any matured pending (chained) events first
    forced = _tick_pending_events(bundle, state)
    rolled.extend(forced)
    excluded.update(e.id for e in forced)

    # Normal random event rolls (skip if a forced event already fired)
    if not forced and rng.random() < bundle.config.primary_event_chance:
        event = pick_event(bundle, state, rng, excluded)
        if event:
            resolve_event(bundle, state, event)
            rolled.append(event)
            excluded.add(event.id)
            if event.choices:
                return rolled
    if rng.random() < bundle.config.secondary_event_chance:
        event = pick_event(bundle, state, rng, excluded)
        if event:
            resolve_event(bundle, state, event)
            rolled.append(event)
            if event.choices:
                return rolled
    return rolled
