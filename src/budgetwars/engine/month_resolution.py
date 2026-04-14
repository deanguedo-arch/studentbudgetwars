from __future__ import annotations

from dataclasses import dataclass
from random import Random

from budgetwars.models import ActiveMonthlyModifier, ContentBundle, GameState

from .budgeting import (
    apply_budget_stance,
    apply_interest_and_growth,
    debt_payment_due,
    discretionary_spending,
    living_cost,
    make_debt_payment,
    pay_named_cost,
)
from .careers import add_promotion_progress, apply_career_effects, current_income, maybe_promote
from .education import apply_education_effects, education_monthly_cost, update_education_progress
from .effects import append_log, apply_stat_effects, clamp_player_state, net_worth, summarize_milestone, trim_logs
from .events import roll_month_events
from .housing import apply_housing_effects, can_switch_housing, monthly_housing_cost
from .lookups import (
    get_career_track,
    get_city,
    get_current_career_tier,
    get_difficulty,
    get_education_program,
    get_focus_action,
    get_housing_option,
    get_transport_option,
)
from .status_arcs import get_active_status_arc, tick_status_arcs
from .transport import apply_transport_access_penalty, apply_transport_effects, can_switch_transport, monthly_transport_cost
from .wealth import apply_wealth_allocations, apply_wealth_pressure_identity, apply_wealth_returns
from .scoring import credit_tier_label, dominant_pressure_family


@dataclass
class ModifierSnapshot:
    income_multiplier: float = 1.0
    housing_cost_delta: int = 0
    living_cost_delta: int = 0
    transport_cost_delta: int = 0
    education_cost_delta: int = 0
    promotion_progress_delta: int = 0
    education_progress_delta: int = 0
    transport_switch_discount: int = 0


def _capture_resource_delta(
    state: GameState,
    *,
    label: str,
    previous_stress: int,
    previous_energy: int,
    stress_parts: list[str],
    energy_parts: list[str],
) -> None:
    stress_delta = state.player.stress - previous_stress
    energy_delta = state.player.energy - previous_energy
    if stress_delta:
        stress_parts.append(f"{label} {stress_delta:+d}")
    if energy_delta:
        energy_parts.append(f"{label} {energy_delta:+d}")


def _apply_start_of_month_modifiers(state: GameState, modifiers: list[ActiveMonthlyModifier]) -> ModifierSnapshot:
    snapshot = ModifierSnapshot()
    for modifier in modifiers:
        apply_stat_effects(state, modifier.stat_effects)
        snapshot.income_multiplier *= modifier.income_multiplier
        snapshot.housing_cost_delta += modifier.housing_cost_delta
        snapshot.living_cost_delta += modifier.living_cost_delta
        snapshot.transport_cost_delta += modifier.transport_cost_delta
        snapshot.education_cost_delta += modifier.education_cost_delta
        snapshot.promotion_progress_delta += modifier.promotion_progress_delta
        snapshot.education_progress_delta += modifier.education_progress_delta
        snapshot.transport_switch_discount += modifier.transport_switch_discount
        append_log(state, f"Active carryover: {modifier.label}")
    return snapshot


def _tick_existing_modifiers(state: GameState, existing_modifier_tokens: set[int]) -> None:
    remaining: list[ActiveMonthlyModifier] = []
    for modifier in state.active_modifiers:
        if id(modifier) in existing_modifier_tokens:
            modifier.remaining_months -= 1
        if modifier.remaining_months > 0:
            remaining.append(modifier)
        else:
            append_log(state, f"{modifier.label} wore off.")
    state.active_modifiers = remaining


def _update_housing_stability(state: GameState, housing_shortfall: int) -> None:
    if housing_shortfall > 0:
        state.player.housing.missed_payment_streak += 1
    else:
        state.player.housing.missed_payment_streak = max(0, state.player.housing.missed_payment_streak - 1)

    if state.player.housing.missed_payment_streak <= state.housing_miss_limit:
        return

    player = state.player
    if (
        player.current_city_id == "hometown_low_cost"
        and player.family_support >= state.minimum_parent_fallback_support
        and player.housing_id != "parents"
    ):
        player.housing.option_id = "parents"
        player.housing.months_in_place = 0
        player.housing.missed_payment_streak = 0
        append_log(state, "Housing slipped badly enough that you moved back in with your parents to stabilize.")
        return
    state.game_over_reason = "housing_loss"


def _update_burnout(state: GameState) -> None:
    if state.player.stress >= state.burnout_stress_threshold or state.player.energy <= state.burnout_energy_threshold:
        state.burnout_streak += 1
    else:
        state.burnout_streak = 0
    if state.burnout_streak > state.burnout_streak_limit:
        state.game_over_reason = "burnout_collapse"


def _update_social_and_family_pressure(state: GameState) -> None:
    if state.player.life_satisfaction <= 35:
        state.player.social_stability -= 2
    if state.player.stress >= 75:
        state.player.social_stability -= 1
    if state.player.family_support <= 25:
        state.player.stress += 1
    if state.player.housing.housing_stability <= 38:
        state.player.social_stability -= 1
        state.player.stress += 1
    if state.player.social_stability <= 30:
        state.player.stress += 2
        state.player.energy -= 1
    if state.player.social_stability >= 70:
        state.player.stress -= 1


def _check_collections(state: GameState) -> None:
    if state.player.debt >= state.debt_game_over_threshold:
        state.game_over_reason = "collections"


def _check_academic_collapse(state: GameState) -> None:
    education = state.player.education
    if education.failure_streak <= state.academic_failure_streak_limit:
        return
    education.is_active = False
    education.is_paused = True
    state.player.life_satisfaction -= 4
    state.player.stress += 5
    append_log(state, "Academic pressure broke the month badly enough that school shut down for now.")
    if state.player.career.track_id == "degree_gated_professional":
        state.game_over_reason = "academic_collapse"


def _update_momentum_and_drag(state: GameState) -> None:
    player = state.player
    if player.monthly_surplus >= 150:
        player.housing.housing_stability = min(100, player.housing.housing_stability + 1)
    elif player.monthly_surplus < -150:
        player.housing.housing_stability = max(0, player.housing.housing_stability - 2)
    if player.debt > 20000:
        player.career.promotion_momentum = max(0, player.career.promotion_momentum - 2)
        player.education.education_momentum = max(0, player.education.education_momentum - 2)
    if player.debt > 32000:
        player.stress += 2
    if player.cash + player.savings + player.high_interest_savings < 250:
        player.life_satisfaction = max(0, player.life_satisfaction - 1)
    if player.family_support < 28 and player.housing_id == "parents":
        player.housing.housing_stability = max(0, player.housing.housing_stability - 2)
        player.stress += 1


def _record_annual_milestone(bundle: ContentBundle, state: GameState) -> None:
    tier = get_current_career_tier(bundle, state)
    summary = summarize_milestone(state, career_tier_label=tier.label)
    summary.summary_lines = [
        f"Age {summary.age}: net worth {summary.net_worth:+d}.",
        f"Income ${summary.monthly_income} vs expenses ${summary.monthly_expenses}.",
        f"Housing: {summary.housing_id.replace('_', ' ')}.",
        f"Career: {summary.career_track_id.replace('_', ' ')} - {summary.career_tier_label}.",
        f"Education: {summary.education_program_id.replace('_', ' ')}.",
        f"Stress {summary.stress}, life satisfaction {summary.life_satisfaction}.",
    ]
    state.annual_milestones.append(summary)
    append_log(state, f"Year {summary.year} closed. You are now age {summary.age}.")


def _build_month_driver_notes(
    state: GameState,
    *,
    regime_name: str,
    housing_cost: int,
    transport_cost: int,
    education_cost: int,
    wealth_allocations: dict[str, int],
) -> list[str]:
    notes: list[str] = []
    player = state.player
    if player.career.transition_penalty_months > 0:
        notes.append("Career transition drag is still cutting reliability and slowing momentum.")
    if player.education.reentry_drag_months > 0:
        notes.append("School re-entry drag is still making education progress heavier than usual.")
    if player.housing.housing_stability <= 45:
        notes.append("Housing instability is leaking into stress and overall life consistency.")
    if player.transport.reliability_score <= 45:
        notes.append("Transport reliability is now turning normal months into scramble months.")
    if player.credit_score < 580:
        notes.append("Credit is now blocking some housing and transport moves.")
    elif player.credit_score < 670:
        notes.append("Credit is fair, but it still narrows the finance and housing lane.")
    if player.credit_missed_obligation_streak >= 2:
        notes.append("Recent missed obligations are now closing financing doors even with okay scores.")
    if player.credit_utilization_pressure >= 72:
        notes.append("Credit utilization pressure is high enough to trigger tougher approvals.")
    if housing_cost >= max(transport_cost * 2, 900):
        notes.append("Housing is one of the biggest forces shaping your monthly margin right now.")
    if transport_cost >= 400:
        notes.append("Transport ownership is eating a meaningful chunk of your monthly cash flow.")
    if education_cost >= 300 and player.education.is_active:
        notes.append("Education cost is buying long-term upside, but it is squeezing the present.")
    if wealth_allocations["growth"] > 0 or wealth_allocations["index"] > 0:
        notes.append(f"{regime_name} market conditions are now affecting your life through invested money.")
    if player.wealth_strategy_id == "market_chaser" and state.current_market_regime_id in {"weak", "correction"}:
        notes.append("Market-chasing posture is amplifying drawdown risk while this regime stays weak.")
    if player.wealth_strategy_id == "cushion_first" and player.high_interest_savings >= 800:
        notes.append("Cushion-first still gives you a liquidity shield when the month turns against you.")
    if player.wealth_strategy_id == "debt_crusher" and player.debt >= 7000 and player.monthly_surplus <= 120:
        notes.append("Debt-crusher is buying long-term relief, but this month has little breathing room.")
    if player.wealth_strategy_id == "steady_builder" and player.monthly_surplus >= 120 and player.debt <= 7000:
        notes.append("Steady-builder is compounding progress without fully giving up monthly flexibility.")
    if player.housing_id == "parents" and player.family_support <= state.minimum_parent_fallback_support + 10:
        notes.append("Staying home is still saving money, but the family buffer is starting to wear thin.")
    if player.housing_id == "roommates" and player.social_stability <= 45:
        notes.append("Roommate living is amplifying instability because your social footing is weak.")
    if player.transport_id == "financed_car" and player.monthly_surplus < 0:
        notes.append("The financed car is acting like a debt trap instead of a mobility win.")
    if player.career.track_id == "sales" and player.career.promotion_momentum >= 65:
        notes.append("Sales momentum is compounding. Good months are opening more upside.")
    if player.career.track_id == "warehouse_logistics" and player.energy <= 30:
        notes.append("Warehouse fatigue is now affecting the rest of your life, not just the job.")
    if player.social_stability <= 35:
        notes.append("Low social stability is making recovery and performance less reliable.")
    return notes[:5]


def _credit_band_id(credit_score: int) -> str:
    if credit_score < 580:
        return "fragile"
    if credit_score < 670:
        return "fair"
    if credit_score < 740:
        return "strong"
    return "prime"


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


def _recovery_modifier(state: GameState, bundle: ContentBundle, key: str) -> float:
    return sum(float(layer.recovery_modifiers.get(key, 0.0)) for layer in _consequence_layers(bundle, state))


def _pressure_map(state: GameState) -> list[tuple[str, int]]:
    player = state.player
    focus_id = player.selected_focus_action_id
    focus_boost = 10 if focus_id in {"overtime", "promotion_hunt"} else 0
    focus_recovery = -8 if focus_id in {"recovery_month", "social_maintenance"} else 0
    work = max(
        0,
        min(
            100,
            player.stress
            + focus_boost
            + max(0, player.career.transition_penalty_months * 8)
            + max(0, player.career.layoff_pressure * 2)
            + focus_recovery,
        ),
    )
    housing = max(0, min(100, (100 - player.housing.housing_stability) + (player.housing.missed_payment_streak * 14)))
    transport = max(0, min(100, (100 - player.transport.reliability_score) + (player.transport.breakdown_pressure * 8)))
    debt = max(
        0,
        min(
            100,
            int(player.debt / 220)
            + (14 if player.monthly_surplus < 0 else 0)
            + (16 if player.credit_score < 580 else 0)
            + (8 if player.credit_score < 670 else 0),
        ),
    )
    education = 0
    if player.education.is_active or player.education.standing < 65:
        intensity_drag = {"light": -6, "standard": 0, "intensive": 10}.get(player.education.intensity_level, 0)
        education = max(
            0,
            min(
                100,
                (100 - player.education.standing)
                + (player.education.failure_streak * 12)
                + intensity_drag,
            ),
        )
    support = max(0, min(100, int((100 - player.social_stability) * 0.6) + max(0, 50 - player.family_support)))
    return sorted(
        [
            ("work overload", work),
            ("housing squeeze", housing),
            ("transport friction", transport),
            ("debt anxiety", debt),
            ("education pressure", education),
            ("support strain", support),
        ],
        key=lambda item: item[1],
        reverse=True,
    )


def _city_stress_bias(bundle: ContentBundle, state: GameState) -> tuple[int, int, str]:
    city = get_city(bundle, state.player.current_city_id)
    if city.id == "hometown_low_cost":
        return (2, 0, "hometown breathing room")
    if city.id == "mid_size_city":
        return (1, 1, "mid-size pace")
    if city.id == "high_opportunity_metro":
        return (0, 2, "metro pace")
    return (0, 1, city.name.lower())


def _active_arc_pressure_bias(state: GameState) -> tuple[int, int, list[str]]:
    recovery_penalty = 0
    pressure_penalty = 0
    labels: list[str] = []
    for arc in state.active_status_arcs:
        if arc.severity >= 2:
            recovery_penalty += arc.severity - 1
            pressure_penalty += 1
            if arc.severity >= 3:
                pressure_penalty += 1
            labels.append(arc.arc_id.replace("_", " "))
    return recovery_penalty, pressure_penalty, labels[:3]


def _stress_recovery_capacity(
    bundle: ContentBundle,
    state: GameState,
    *,
    difficulty_stress_multiplier: float = 1.0,
) -> tuple[int, list[str]]:
    player = state.player
    capacity = 5
    reasons: list[str] = []

    focus_id = player.selected_focus_action_id
    if focus_id == "recovery_month":
        capacity += 7
        reasons.append("recovery month")
    elif focus_id == "social_maintenance":
        capacity += 4
        reasons.append("social maintenance")
    elif focus_id == "move_prep":
        capacity += 2
        reasons.append("move prep")

    if player.housing.housing_stability >= 70:
        capacity += 2
        reasons.append("stable housing")
    elif player.housing.housing_stability >= 55:
        capacity += 1
        reasons.append("okay housing")
    elif player.housing.housing_stability <= 40:
        capacity -= 2

    if player.transport.reliability_score >= 80:
        capacity += 2
        reasons.append("reliable transport")
    elif player.transport.reliability_score >= 65:
        capacity += 1
        reasons.append("usable transport")
    elif player.transport.reliability_score <= 50:
        capacity -= 2

    if player.social_stability >= 65:
        capacity += 2
        reasons.append("strong social footing")
    elif player.social_stability >= 50:
        capacity += 1
        reasons.append("steady support")
    elif player.social_stability <= 35:
        capacity -= 2

    if player.family_support >= 60:
        capacity += 1
        reasons.append("family buffer")
    elif player.family_support <= 30:
        capacity -= 1

    liquid_buffer = player.cash + player.savings + player.high_interest_savings
    if liquid_buffer >= 2500:
        capacity += 2
        reasons.append("cash cushion")
    elif liquid_buffer >= 1000:
        capacity += 1
        reasons.append("some buffer")
    elif liquid_buffer < 250:
        capacity -= 1

    if player.energy >= 65:
        capacity += 1
        reasons.append("good energy")
    elif player.energy <= 35:
        capacity -= 2

    city_recovery_bias, _, city_label = _city_stress_bias(bundle, state)
    capacity += city_recovery_bias
    if city_recovery_bias > 0:
        reasons.append(city_label)

    recovery_penalty, _, arc_labels = _active_arc_pressure_bias(state)
    if recovery_penalty:
        capacity -= recovery_penalty
        reasons.append(f"arc drag: {', '.join(arc_labels)}")

    if difficulty_stress_multiplier < 1.0:
        capacity += 1
        reasons.append("easy mode breathing room")
    elif difficulty_stress_multiplier > 1.0:
        capacity -= 1

    return max(0, capacity), reasons[:4]


def _stress_pressure_burden(
    bundle: ContentBundle,
    state: GameState,
    top_pressures: list[tuple[str, int]],
    *,
    difficulty_stress_multiplier: float = 1.0,
) -> tuple[int, list[str]]:
    player = state.player
    if not top_pressures:
        return (0, ["no dominant pressure"])

    avg = sum(value for _, value in top_pressures) / len(top_pressures)
    burden = max(0, int(round(avg / 18)))
    reasons = [top_pressures[0][0]]

    if player.stress >= 75:
        burden += 2
        reasons.append("high current stress")
    elif player.stress >= 60:
        burden += 1
        reasons.append("elevated stress")

    if player.energy <= 35:
        burden += 2
        reasons.append("low energy")
    elif player.energy <= 50:
        burden += 1
        reasons.append("soft energy")

    if player.debt >= 10000 or player.credit_score < 580:
        burden += 1
        reasons.append("debt pressure")

    _, city_pressure_bias, city_label = _city_stress_bias(bundle, state)
    burden += city_pressure_bias
    if city_pressure_bias:
        reasons.append(city_label)

    if player.selected_focus_action_id in {"overtime", "promotion_hunt"}:
        burden += 1
        reasons.append("push focus")

    _, pressure_penalty, arc_labels = _active_arc_pressure_bias(state)
    if pressure_penalty:
        burden += pressure_penalty
        reasons.append(f"active arcs: {', '.join(arc_labels)}")

    if difficulty_stress_multiplier < 1.0:
        burden = max(0, burden - 1)
    elif difficulty_stress_multiplier > 1.0:
        burden += 1
        reasons.append("hard mode squeeze")

    return burden, reasons[:4]


def _apply_pressure_dynamics(
    bundle: ContentBundle,
    state: GameState,
    *,
    difficulty_stress_multiplier: float = 1.0,
) -> tuple[list[str], str, str]:
    pressures = _pressure_map(state)
    top = [(name, value) for name, value in pressures if value > 0][:3]
    if not top:
        return (
            ["stable: no major pressure source is dominating"],
            "stable (+0 stress)",
            "Recovery balance: 0 capacity vs 0 pressure (quiet month).",
        )

    recovery_capacity, recovery_reasons = _stress_recovery_capacity(
        bundle,
        state,
        difficulty_stress_multiplier=difficulty_stress_multiplier,
    )
    pressure_burden, pressure_reasons = _stress_pressure_burden(
        bundle,
        state,
        top,
        difficulty_stress_multiplier=difficulty_stress_multiplier,
    )
    avg = sum(value for _, value in top) / len(top)
    net = recovery_capacity - pressure_burden
    if net >= 16:
        stress_shift = -5
    elif net >= 12:
        stress_shift = -4
    elif net >= 8:
        stress_shift = -3
    elif net >= 4:
        stress_shift = -2
    elif net >= 1:
        stress_shift = -1
    elif net <= -7:
        stress_shift = 4
    elif net <= -4:
        stress_shift = 3
    elif net <= -2:
        stress_shift = 2
    elif net < 0:
        stress_shift = 1
    else:
        stress_shift = 0

    if state.player.selected_focus_action_id in {"overtime", "promotion_hunt"}:
        if avg >= 42:
            stress_shift = max(stress_shift, 2)
        elif avg >= 30:
            stress_shift = max(stress_shift, 1)

    if (
        stress_shift == 0
        and state.player.selected_focus_action_id in {"recovery_month", "social_maintenance"}
        and difficulty_stress_multiplier <= 1.0
    ):
        stress_shift = -1

    state.player.stress += stress_shift
    labels = [f"{name} {value}" for name, value in top]
    if stress_shift > 0:
        trend = f"rising (+{stress_shift} stress)"
    elif stress_shift < 0:
        trend = f"easing ({stress_shift} stress)"
    else:
        trend = "stable (+0 stress)"
    balance_line = (
        "Recovery balance: "
        f"{recovery_capacity} capacity vs {pressure_burden} pressure "
        f"({', '.join(recovery_reasons[:2]) or 'limited recovery'} vs "
        f"{', '.join(pressure_reasons[:2]) or 'light pressure'})."
    )
    return labels, trend, balance_line


def _apply_recovery_routes(state: GameState, bundle: ContentBundle) -> None:
    player = state.player
    current_year = ((state.current_month - 1) // 12) + 1
    if (
        player.stress >= 78
        and player.social_stability >= 74
        and player.family_support >= 62
        and player.last_social_lifeline_year < current_year
    ):
        player.last_social_lifeline_year = current_year
        player.stress -= 6
        player.energy += 4
        player.family_support -= 8
        append_log(state, "Recovery route: your network absorbed part of the crash this month.")
    if (
        player.credit_score >= 705
        and player.debt >= 2600
        and player.monthly_surplus >= 0
        and player.housing.missed_payment_streak == 0
        and player.credit_missed_obligation_streak == 0
        and player.credit_utilization_pressure <= 78
    ):
        debt_relief = min(520, max(200, int(player.debt * 0.045)))
        if player.credit_score >= 760 or player.credit_rebuild_streak >= 2:
            debt_relief = min(620, debt_relief + 90)
        player.debt = max(0, player.debt - debt_relief)
        player.credit_rebuild_streak += 1
        player.stress -= 1
        append_log(state, f"Recovery route: strong credit unlocked debt relief (-${debt_relief}).")
    if (
        player.credit_score <= 590
        and player.debt <= 4500
        and player.monthly_surplus >= 120
        and player.housing.missed_payment_streak == 0
        and (player.cash + player.savings) >= 1000
        and player.credit_missed_obligation_streak == 0
    ):
        credit_gain = 4 if player.credit_score < 575 else 3
        if player.credit_rebuild_streak >= 2:
            credit_gain += 1
        player.credit_score += credit_gain
        player.credit_rebuild_streak += 1
        player.stress -= 1
        append_log(state, f"Recovery route: clean-month credit rebuild added +{credit_gain} credit.")
    if (
        player.housing.housing_stability <= 34
        and player.current_city_id == "hometown_low_cost"
        and player.family_support >= bundle.config.minimum_parent_fallback_support + 8
        and player.housing.option_id != "parents"
    ):
        player.housing.option_id = "parents"
        player.housing.months_in_place = 0
        player.housing.missed_payment_streak = 0
        player.housing.housing_stability = max(player.housing.housing_stability, 52)
        player.stress -= 3
        append_log(state, "Recovery route: moved back home to stop a housing spiral.")
    if (
        player.housing.option_id in {"roommates", "solo_rental"}
        and player.housing.housing_stability <= 35
        and (player.housing.missed_payment_streak > 0 or player.monthly_surplus < 0)
        and ((player.savings + player.high_interest_savings) >= 900 or player.emergency_liquidation_count > 0)
        and player.wealth_strategy_id in {"cushion_first", "steady_builder"}
    ):
        reserve_spend = 0
        if (player.savings + player.high_interest_savings) >= 900:
            reserve_spend = min(420, max(180, int((player.savings + player.high_interest_savings) * 0.12)))
            from_savings = min(player.savings, reserve_spend)
            player.savings -= from_savings
            remaining = reserve_spend - from_savings
            from_safe = min(player.high_interest_savings, remaining)
            player.high_interest_savings -= from_safe
            reserve_spend = from_savings + from_safe
        player.housing.missed_payment_streak = 0
        player.housing.housing_stability = max(player.housing.housing_stability, 42)
        player.stress -= 2
        if reserve_spend > 0:
            append_log(state, f"Recovery route: cash reserve buffer stabilized housing (-${reserve_spend}).")
        else:
            append_log(state, "Recovery route: your cash reserve buffer softened the housing spiral after liquidation.")
    if (
        player.transport.option_id in {"financed_car", "luxury_financed_car"}
        and player.monthly_surplus <= -120
        and player.debt >= 9000
        and player.credit_score < 680
        and (player.cash + player.savings) < 500
    ):
        player.transport.option_id = "transit"
        player.transport.months_owned = 0
        player.transport.reliability_score = max(player.transport.reliability_score, 78)
        player.transport.recent_switch_penalty_months = 0
        player.stress -= 2
        player.life_satisfaction -= 1
        append_log(state, "Recovery route: transport downgrade cut the financed trap and restored monthly oxygen.")
    if (
        player.career.branch_id is not None
        and state.current_month >= 18
        and player.stress >= 84
        and player.energy <= 30
        and player.monthly_surplus <= -120
        and player.debt >= 9000
        and (player.career.promotion_momentum <= 45 or player.career.layoff_pressure >= 10)
    ):
        prior_branch = player.career.branch_id
        player.career.branch_id = None
        state.pending_promotion_branch_track_id = player.career.track_id
        player.career.tier_index = max(0, player.career.tier_index - 1)
        player.career.promotion_progress = min(player.career.promotion_progress, 2)
        player.career.transition_penalty_months = max(player.career.transition_penalty_months, 2)
        player.stress -= 3
        player.energy += 2
        player.life_satisfaction -= 2
        player.social_stability += 1
        append_log(
            state,
            "Recovery route: branch reset traded title momentum for survival runway "
            f"({prior_branch.replace('_', ' ')} reset).",
        )
    program = get_education_program(bundle, player.education.program_id)
    if (
        player.education.is_active
        and program.can_pause
        and player.education.intensity_level in {"intensive", "standard"}
        and player.stress >= 72
        and player.energy <= 42
        and player.monthly_surplus <= 40
        and (player.cash + player.savings) >= 280
        and (player.cash + player.savings) <= 1300
    ):
        next_intensity = "standard" if player.education.intensity_level == "intensive" else "light"
        if next_intensity != player.education.intensity_level:
            player.education.intensity_level = next_intensity
            player.education.education_momentum = min(100, player.education.education_momentum + 3)
            player.stress -= 2
            player.energy += 2
            append_log(
                state,
                f"Recovery route: de-intensified education to {next_intensity} so the school lane stays alive.",
            )
    if (
        player.education.is_active
        and program.can_pause
        and player.stress >= 82
        and player.energy <= 28
        and player.monthly_surplus < 0
        and (player.cash + player.savings) < 400
    ):
        player.education.is_active = False
        player.education.is_paused = True
        player.education.reentry_drag_months = max(player.education.reentry_drag_months, 1)
        player.stress -= 3
        player.energy += 2
        append_log(state, "Recovery route: paused education to prevent burnout collapse and stabilize cash.")


def _best_recovery_route_line(state: GameState, bundle: ContentBundle) -> str | None:
    player = state.player
    current_year = ((state.current_month - 1) // 12) + 1
    credit_arc = get_active_status_arc(state, "credit_squeeze")
    lease_arc = get_active_status_arc(state, "lease_pressure")
    if (
        player.social_stability >= 74
        and player.family_support >= 62
        and player.last_social_lifeline_year == current_year
    ):
        return "Recovery route: network bailout softened the month."
    if (
        player.credit_score >= 705
        and player.debt >= 2000
        and player.monthly_surplus >= 0
        and player.housing.missed_payment_streak == 0
        and player.credit_missed_obligation_streak == 0
        and player.credit_utilization_pressure <= 78
    ):
        return "Recovery route: strong credit kept debt relief available."
    if (
        player.credit_score <= 590
        and player.debt <= 4500
        and player.monthly_surplus >= 120
        and player.housing.missed_payment_streak == 0
        and player.credit_missed_obligation_streak == 0
    ):
        return "Recovery route: clean months are rebuilding a fragile credit file."
    if (
        credit_arc is not None
        and player.wealth_strategy_id == "debt_crusher"
        and player.monthly_surplus >= 0
        and player.credit_missed_obligation_streak == 0
    ):
        return "Recovery route: debt-crusher cleanup can compress the credit squeeze."
    if player.housing.option_id == "parents" and player.current_city_id == "hometown_low_cost":
        return "Recovery route: family fallback is holding the housing line."
    if (
        lease_arc is not None
        and player.wealth_strategy_id in {"cushion_first", "steady_builder"}
        and (player.savings + player.high_interest_savings) >= 900
    ):
        return "Recovery route: reserve deployment can buy lease runway."
    if player.transport.option_id == "transit" and player.monthly_surplus <= 0 and player.debt >= 9000:
        return "Recovery route: transport downgrade reduced the financed-car trap."
    if (
        player.career.branch_id is None
        and state.pending_promotion_branch_track_id == player.career.track_id
        and player.career.transition_penalty_months > 0
        and player.career.tier_index >= 1
    ):
        return "Recovery route: branch reset bought survival room at the cost of momentum."
    if player.education.is_active and player.education.intensity_level in {"standard", "light"} and player.stress >= 68:
        return "Recovery route: education de-intensify is preserving the school lane."
    if player.education.is_paused and player.education.reentry_drag_months > 0:
        return "Recovery route: paused education to stop a burnout spiral."
    if player.wealth_strategy_id in {"cushion_first", "steady_builder"} and player.housing.housing_stability >= 42:
        return "Recovery route: cash buffer kept the housing spiral from getting worse."
    return None


def _blocked_door_lines(state: GameState, bundle: ContentBundle) -> list[str]:
    player = state.player
    blocked: list[str] = []
    if player.housing.option_id != "solo_rental":
        allowed, reason = can_switch_housing(bundle, state, "solo_rental")
        if not allowed and ("credit" in reason.lower() or "debt" in reason.lower() or "lease" in reason.lower()):
            blocked.append(f"Blocked door: solo rental - {reason}")
    if player.transport.option_id != "financed_car":
        allowed, reason = can_switch_transport(bundle, state, "financed_car")
        if not allowed and (
            "credit" in reason.lower()
            or "debt" in reason.lower()
            or "payment" in reason.lower()
            or "cash" in reason.lower()
        ):
            blocked.append(f"Blocked door: financed car - {reason}")
    return blocked


def _apply_system_signatures(bundle: ContentBundle, state: GameState) -> None:
    player = state.player
    shortfall = max(0, -player.monthly_surplus)
    if shortfall > 0:
        cash_shock_mod = _recovery_modifier(state, bundle, "cash_shock")
        base_penalty = max(1, shortfall // 700)
        stress_penalty = max(0, int(round(base_penalty * (1.0 - cash_shock_mod))))
        if stress_penalty > 0:
            player.stress += stress_penalty
            append_log(state, f"Cash shock pressure: +{stress_penalty} stress from shortfall.")

    stress_recovery_mod = _recovery_modifier(state, bundle, "stress_recovery")
    if stress_recovery_mod > 0:
        recovery = max(1, int(round(stress_recovery_mod * 4)))
        player.stress -= recovery
        append_log(state, f"Recovery posture helped: -{recovery} stress.")

    if state.current_market_regime_id in {"weak", "correction"}:
        exposure = player.index_fund + player.aggressive_growth_fund
        if exposure > 0 and player.wealth_strategy_id == "market_chaser":
            stress_hit = 2 if exposure >= 4000 else 1
            player.stress += stress_hit
            player.life_satisfaction -= 1
            append_log(state, "Market-chasing posture amplified downturn pressure.")
        elif (
            exposure > 0
            and player.wealth_strategy_id == "cushion_first"
            and player.high_interest_savings >= bundle.config.emergency_fund_floor
        ):
            player.stress -= 1
            append_log(state, "Cash-cushion posture absorbed some market stress.")

    track = get_career_track(bundle, player.career.track_id)
    transport = get_transport_option(bundle, player.transport_id)
    if transport.access_level >= track.minimum_transport_access + 1 and player.transport.reliability_score >= 80:
        player.career.promotion_momentum = min(100, player.career.promotion_momentum + 1)
        append_log(state, "Reliable transport consistency boosted career momentum.")

    if player.education.is_active:
        if player.education.standing >= 70 and player.stress <= 60 and player.energy >= 45:
            player.career.promotion_momentum = min(100, player.career.promotion_momentum + 1)
            append_log(state, "Strong school stability translated into better work momentum.")
        elif player.education.standing <= 50 or (player.stress >= 75 and player.energy <= 30):
            player.career.promotion_momentum = max(0, player.career.promotion_momentum - 2)
            append_log(state, "Education drag is now pulling career momentum down.")


def _apply_credit_drift(
    state: GameState,
    *,
    debt_start: int,
    debt_due: int,
    debt_paid: int,
    housing_shortfall: int,
) -> None:
    player = state.player
    credit_adjustment = 0
    credit_parts: list[str] = []
    liquid_buffer = player.cash + player.savings + player.high_interest_savings
    debt_load_ratio = player.debt / max(1, player.monthly_income * 6)

    missed_debt_obligation = debt_due > 0 and debt_paid < debt_due
    missed_housing_obligation = housing_shortfall > 0
    heavy_shortfall = player.monthly_surplus < -80
    missed_obligation_month = missed_debt_obligation or missed_housing_obligation or heavy_shortfall
    clean_obligation_month = housing_shortfall == 0 and (debt_due == 0 or debt_paid >= debt_due) and player.monthly_surplus >= 120
    strong_rebuild_month = clean_obligation_month and player.debt <= debt_start and liquid_buffer >= 1000

    if missed_obligation_month:
        player.credit_missed_obligation_streak += 1
        player.credit_rebuild_streak = 0
    else:
        if strong_rebuild_month:
            player.credit_missed_obligation_streak = 0
        else:
            player.credit_missed_obligation_streak = max(0, player.credit_missed_obligation_streak - 1)
        if strong_rebuild_month:
            player.credit_rebuild_streak += 1
        elif clean_obligation_month:
            player.credit_rebuild_streak = max(0, player.credit_rebuild_streak)
        else:
            player.credit_rebuild_streak = max(0, player.credit_rebuild_streak - 1)

    utilization_raw = int(
        round((player.debt / max(1, (player.monthly_income * 5) + liquid_buffer + 1200)) * 100)
    )
    if player.monthly_surplus < 0:
        utilization_raw += 8
    if player.debt > debt_start:
        utilization_raw += 6
    if player.credit_missed_obligation_streak >= 2:
        utilization_raw += 10
    if player.credit_rebuild_streak >= 2:
        utilization_raw -= 8
    utilization_raw = max(0, min(100, utilization_raw))
    player.credit_utilization_pressure = int(
        round((player.credit_utilization_pressure * 0.55) + (utilization_raw * 0.45))
    )
    player.credit_utilization_pressure = max(0, min(100, player.credit_utilization_pressure))

    if debt_due > 0 and debt_paid >= debt_due:
        credit_adjustment += 1
        credit_parts.append("on-time debt payment +1")
    elif debt_due > 0 and debt_paid < debt_due:
        credit_adjustment -= 7
        credit_parts.append("missed debt payment -7")
    if housing_shortfall > 0:
        credit_adjustment -= 5
        credit_parts.append("housing shortfall -5")
    if player.monthly_surplus < -300:
        credit_adjustment -= 3
        credit_parts.append("negative swing -3")
    elif player.monthly_surplus < 0:
        credit_adjustment -= 2
        credit_parts.append("soft shortfall -2")
    if debt_load_ratio >= 2.0:
        credit_adjustment -= 3
        credit_parts.append("heavy debt ratio -3")
    elif debt_load_ratio >= 1.25:
        credit_adjustment -= 2
        credit_parts.append("debt ratio drag -2")
    elif debt_load_ratio >= 0.75:
        credit_adjustment -= 1
        credit_parts.append("carried leverage -1")
    if player.debt >= 18000:
        credit_adjustment -= 5
        credit_parts.append("heavy debt load -5")
    elif player.debt >= 10000:
        credit_adjustment -= 3
        credit_parts.append("high debt load -3")
    elif player.debt >= 7000:
        credit_adjustment -= 3
        credit_parts.append("debt load -3")
    elif player.debt >= 4000:
        credit_adjustment -= 2
        credit_parts.append("debt load -2")
    if player.debt >= 7000 and player.credit_score < 720:
        credit_adjustment -= 1
        credit_parts.append("credit utilization drag -1")
    if player.debt > debt_start:
        credit_adjustment -= 2
        credit_parts.append("debt trend worse -2")
    if player.debt < debt_start and player.monthly_surplus >= 0 and player.debt < 5000:
        credit_adjustment += 1
        credit_parts.append("debt trend improving +1")
    if housing_shortfall == 0 and debt_due == 0 and player.monthly_surplus >= 150 and player.debt < 6000 and liquid_buffer >= 1000:
        credit_adjustment += 1
        credit_parts.append("clean obligations month +1")
    elif housing_shortfall == 0 and debt_paid >= debt_due and player.monthly_surplus >= 150 and player.debt < 6000 and liquid_buffer >= 1000:
        credit_adjustment += 2
        credit_parts.append("clean on-time month +2")
    if liquid_buffer >= 1500 and player.monthly_surplus >= 100 and debt_load_ratio < 0.75:
        credit_adjustment += 1
        credit_parts.append("buffer plus low leverage +1")
    if player.debt >= 7000 and liquid_buffer < 800:
        credit_adjustment -= 2
        credit_parts.append("thin buffer under debt -2")
    if player.credit_missed_obligation_streak >= 1:
        streak_penalty = min(6, 1 + player.credit_missed_obligation_streak)
        credit_adjustment -= streak_penalty
        credit_parts.append(f"obligation streak -{streak_penalty}")
    if player.credit_utilization_pressure >= 80:
        credit_adjustment -= 4
        credit_parts.append("utilization pressure -4")
    elif player.credit_utilization_pressure >= 68:
        credit_adjustment -= 3
        credit_parts.append("utilization pressure -3")
    elif player.credit_utilization_pressure >= 55:
        credit_adjustment -= 2
        credit_parts.append("utilization pressure -2")
    if player.credit_rebuild_streak >= 2:
        rebuild_bonus = 2 if player.credit_rebuild_streak >= 4 else 1
        credit_adjustment += rebuild_bonus
        credit_parts.append(f"rebuild streak +{rebuild_bonus}")
    if player.credit_rebuild_streak >= 5 and player.credit_score < 670:
        credit_adjustment += 1
        credit_parts.append("sustained rebuild +1")
    if player.credit_score < 620 and player.monthly_surplus >= 180 and player.debt <= debt_start:
        credit_adjustment += 1
        credit_parts.append("credit rebuild pace +1")
    if player.credit_score < 580 and housing_shortfall == 0 and player.monthly_surplus >= 180 and player.debt <= debt_start:
        credit_adjustment += 2
        credit_parts.append("fragile-credit rebuild push +2")
    elif player.credit_score < 670 and housing_shortfall == 0 and player.monthly_surplus >= 180 and player.debt <= debt_start:
        credit_adjustment += 1
        credit_parts.append("fair-credit rebuild push +1")
    credit_adjustment = max(-12, min(8, credit_adjustment))
    if credit_adjustment:
        player.credit_score = max(300, min(850, player.credit_score + credit_adjustment))
        append_log(state, f"Credit drift: {credit_adjustment:+d} ({', '.join(credit_parts)})")
    append_log(
        state,
        "Credit profile: "
        f"missed streak {player.credit_missed_obligation_streak}, "
        f"rebuild streak {player.credit_rebuild_streak}, "
        f"utilization pressure {player.credit_utilization_pressure}.",
    )


def _apply_focus_life_floor(state: GameState, *, focus_id: str, life_start: int) -> None:
    if focus_id not in {"recovery_month", "social_maintenance"}:
        return
    minimum_gain = 2 if focus_id == "recovery_month" else 1
    target = life_start + minimum_gain
    if state.player.life_satisfaction >= target:
        return
    boost = target - state.player.life_satisfaction
    state.player.life_satisfaction += boost
    append_log(state, f"Well-being focus converted into +{boost} life stability.")


def resolve_month(bundle: ContentBundle, state: GameState, rng: Random) -> None:
    if state.game_over_reason or state.current_month > state.total_months:
        return
    _check_collections(state)
    if state.game_over_reason:
        return

    start_net = net_worth(state)
    stress_start = state.player.stress
    energy_start = state.player.energy
    life_start = state.player.life_satisfaction
    credit_start = state.player.credit_score
    stress_parts: list[str] = []
    energy_parts: list[str] = []
    existing_modifier_tokens = {id(modifier) for modifier in state.active_modifiers}
    state.recent_summary = []
    state.month_driver_notes = []
    append_log(state, f"--- Month {state.current_month} / Year {state.current_year} (Age {state.current_age}) ---")

    housing = get_housing_option(bundle, state.player.housing_id)
    difficulty = get_difficulty(bundle, state.difficulty_id)
    debt_start = state.player.debt
    housing_energy_recovery = int(round((housing.recovery_score - 50) / 12))
    housing_stress_relief = int(round((housing.recovery_score - 50) / 18))
    difficulty_stress_relief = max(0, int(round((1.0 - difficulty.stress_multiplier) * 20)))
    baseline_energy_recovery = bundle.config.baseline_monthly_energy_recovery + housing_energy_recovery
    baseline_stress_relief = bundle.config.baseline_monthly_stress_relief + housing_stress_relief + difficulty_stress_relief
    state.player.energy += baseline_energy_recovery
    state.player.stress -= baseline_stress_relief
    stress_parts.append(f"baseline {-baseline_stress_relief:+d}")
    energy_parts.append(f"baseline {baseline_energy_recovery:+d}")

    before_stress = state.player.stress
    before_energy = state.player.energy
    snapshot = _apply_start_of_month_modifiers(state, list(state.active_modifiers))
    _capture_resource_delta(
        state,
        label="carryover",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )
    focus = get_focus_action(bundle, state.player.selected_focus_action_id)

    before_stress = state.player.stress
    before_energy = state.player.energy
    access_multiplier = apply_transport_access_penalty(bundle, state)
    _capture_resource_delta(
        state,
        label="access",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )
    income = current_income(bundle, state, snapshot.income_multiplier * focus.income_multiplier * access_multiplier)
    state.player.cash += income
    state.player.monthly_income = income
    append_log(state, f"Income from {state.player.career.track_id.replace('_', ' ')}: ${income}")

    before_stress = state.player.stress
    before_energy = state.player.energy
    apply_career_effects(bundle, state)
    _capture_resource_delta(
        state,
        label="work",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )

    before_stress = state.player.stress
    before_energy = state.player.energy
    apply_education_effects(bundle, state)
    _capture_resource_delta(
        state,
        label="school",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )
    education_cost = education_monthly_cost(bundle, state, modifier_delta=snapshot.education_cost_delta)
    if education_cost:
        pay_named_cost(state, education_cost, "Education")

    housing_cost = monthly_housing_cost(bundle, state, modifier_delta=snapshot.housing_cost_delta)
    housing_payment = pay_named_cost(state, housing_cost, "Housing")

    before_stress = state.player.stress
    before_energy = state.player.energy
    apply_housing_effects(bundle, state)
    _capture_resource_delta(
        state,
        label="housing",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )

    transport_cost = monthly_transport_cost(bundle, state, modifier_delta=snapshot.transport_cost_delta)
    if transport_cost:
        pay_named_cost(state, transport_cost, "Transport")

    before_stress = state.player.stress
    before_energy = state.player.energy
    apply_transport_effects(bundle, state)
    _capture_resource_delta(
        state,
        label="transport",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )

    living = living_cost(bundle, state, modifier_delta=snapshot.living_cost_delta)
    pay_named_cost(state, living, "Living costs")

    debt_due = debt_payment_due(bundle, state)
    debt_paid = 0
    if debt_due:
        debt_paid = make_debt_payment(state, debt_due)

    discretionary = discretionary_spending(bundle, state)
    if discretionary:
        pay_named_cost(state, discretionary, "Discretionary spending")

    before_stress = state.player.stress
    before_energy = state.player.energy
    savings_transfer = apply_budget_stance(bundle, state, state.player.cash)
    _capture_resource_delta(
        state,
        label="budget",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )

    before_stress = state.player.stress
    before_energy = state.player.energy
    state.player.stress += focus.stress_delta
    state.player.energy += focus.energy_delta
    state.player.life_satisfaction += focus.life_satisfaction_delta
    state.player.social_stability += focus.social_stability_delta
    apply_stat_effects(state, focus.stat_effects)
    _capture_resource_delta(
        state,
        label=focus.name.lower(),
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )
    append_log(state, f"Focus for the month: {focus.name}")

    wealth_allocations = apply_wealth_allocations(bundle, state)

    before_stress = state.player.stress
    before_energy = state.player.energy
    roll_month_events(bundle, state, rng)
    _capture_resource_delta(
        state,
        label="events",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )

    add_promotion_progress(bundle, state, focus.promotion_progress_bonus + snapshot.promotion_progress_delta)
    update_education_progress(bundle, state, focus.education_progress_bonus + snapshot.education_progress_delta)
    maybe_promote(bundle, state)

    interest, savings_growth = apply_interest_and_growth(bundle, state)
    safe_gain, index_gain, growth_gain, regime_name = apply_wealth_returns(bundle, state, rng)
    _update_social_and_family_pressure(state)
    clamp_player_state(state)
    _tick_existing_modifiers(state, existing_modifier_tokens)
    _update_housing_stability(state, housing_payment.added_to_debt)
    _update_burnout(state)
    _check_academic_collapse(state)
    _check_collections(state)

    monthly_expenses = housing_cost + transport_cost + living + education_cost + debt_paid + discretionary
    state.player.monthly_expenses = monthly_expenses
    end_net = net_worth(state)
    state.player.monthly_surplus = end_net - start_net
    apply_wealth_pressure_identity(bundle, state)
    _update_momentum_and_drag(state)
    _apply_system_signatures(bundle, state)
    pressure_top, pressure_trend, recovery_balance = _apply_pressure_dynamics(
        bundle,
        state,
        difficulty_stress_multiplier=difficulty.stress_multiplier,
    )
    _apply_recovery_routes(state, bundle)
    _apply_credit_drift(
        state,
        debt_start=debt_start,
        debt_due=debt_due,
        debt_paid=debt_paid,
        housing_shortfall=housing_payment.added_to_debt,
    )
    _apply_focus_life_floor(state, focus_id=focus.id, life_start=life_start)
    clamp_player_state(state)
    state.month_driver_notes = _build_month_driver_notes(
        state,
        regime_name=regime_name,
        housing_cost=housing_cost,
        transport_cost=transport_cost,
        education_cost=education_cost,
        wealth_allocations=wealth_allocations,
    )
    state.recent_summary = [
        f"Income ${income}",
        f"Expenses ${monthly_expenses}",
        f"Housing ${housing_cost}",
        f"Transport ${transport_cost}",
        f"Education ${education_cost}",
        f"Living ${living}",
        f"Debt {'payment $' + str(debt_paid) if debt_paid else 'steady'}",
        f"Savings transfer ${savings_transfer}",
        (
            "Wealth allocation "
            f"safe ${wealth_allocations['safe']}, index ${wealth_allocations['index']}, "
            f"growth ${wealth_allocations['growth']}, debt ${wealth_allocations['extra_debt']}"
        ),
        f"Interest +${interest} / Growth +${savings_growth}",
        (
            f"Market {regime_name}: safe {safe_gain:+d}, index {index_gain:+d}, "
            f"growth {growth_gain:+d}"
        ),
        f"Month swing {state.player.monthly_surplus:+d}",
        f"Credit {credit_start}->{state.player.credit_score} ({state.player.credit_score - credit_start:+d})",
        f"Credit tier: {credit_tier_label(state.player.credit_score)}",
        f"Situation family: {dominant_pressure_family(state)}",
        "Pressure map: " + ", ".join(pressure_top),
        recovery_balance,
        f"Pressure trend: {pressure_trend}",
        f"Stress {stress_start}->{state.player.stress} ({state.player.stress - stress_start:+d})",
        "Stress drivers: " + (", ".join(stress_parts) if stress_parts else "steady"),
        f"Energy {energy_start}->{state.player.energy} ({state.player.energy - energy_start:+d})",
        "Energy drivers: " + (", ".join(energy_parts) if energy_parts else "steady"),
    ]
    recovery_route_line = _best_recovery_route_line(state, bundle)
    if recovery_route_line:
        state.recent_summary.append(recovery_route_line)
    state.recent_summary.extend(_blocked_door_lines(state, bundle))
    if state.game_over_reason:
        append_log(state, f"Run ended: {state.game_over_reason.replace('_', ' ')}.")
    elif state.current_month % 12 == 0:
        _record_annual_milestone(bundle, state)

    tick_status_arcs(bundle, state)
    trim_logs(bundle, state)
    if not state.game_over_reason:
        state.current_month += 1
