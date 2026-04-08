from __future__ import annotations

from random import Random

from budgetwars.models import ContentBundle, EventChoice, EventDefinition, GameState, PendingEvent

from .effects import append_log, apply_stat_effects, create_modifier
from .lookups import get_city, get_housing_option, get_transport_option

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
    if any(token in combined for token in ("layoff", "promotion", "sales", "job", "career", "gig", "work")):
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
    if event.eligible_education_ids and player.education.program_id not in event.eligible_education_ids:
        return False
    if event.eligible_opening_path_ids and player.opening_path_id not in event.eligible_opening_path_ids:
        return False
    if event.eligible_modifier_ids and not set(event.eligible_modifier_ids).issubset(active_modifier_ids):
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
    if event.id == "used_car_window" and transport.access_level >= 3:
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
    if event.id == "refinance_window":
        if state.player.credit_score >= 700:
            weight *= 1.8
        elif state.player.credit_score >= 670:
            weight *= 1.2
        else:
            weight *= 0.25
        if state.player.debt >= 2500:
            weight *= 1.15

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
    state.pending_user_choice_event_id = None
    state.pending_user_choice_event = None
    append_log(state, f"Choice made: {event.name} -> {choice.label}")
    if choice.description:
        append_log(state, choice.description)
    return choice


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
