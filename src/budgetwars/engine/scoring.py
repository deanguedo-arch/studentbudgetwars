from __future__ import annotations

from budgetwars.models import ContentBundle, FinalScoreSummary, GameState, LiveScoreSnapshot

from .effects import net_worth
from .lookups import get_career_track, get_housing_option


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


def _current_branch(bundle: ContentBundle, state: GameState):
    branch_id = state.player.career.branch_id
    if not branch_id:
        return None
    track = get_career_track(bundle, state.player.career.track_id)
    return next((branch for branch in track.branches if branch.id == branch_id), None)


def _score_tier_label(score: float) -> str:
    if score >= 80:
        return "Elite"
    if score >= 60:
        return "Gold"
    if score >= 40:
        return "Silver"
    return "Bronze"


def credit_tier_label(credit_score: int) -> str:
    if credit_score >= 740:
        return "Prime"
    if credit_score >= 670:
        return "Strong"
    if credit_score >= 580:
        return "Fair"
    return "Fragile"


def credit_progress_summary(credit_score: int) -> tuple[str, str, float]:
    if credit_score < 580:
        return "Credit to Fair", f"{580 - credit_score:.0f} points", _clamp_score((credit_score - 300) / 280)
    if credit_score < 670:
        return "Credit to Strong", f"{670 - credit_score:.0f} points", _clamp_score((credit_score - 580) / 90)
    if credit_score < 740:
        return "Credit to Prime", f"{740 - credit_score:.0f} points", _clamp_score((credit_score - 670) / 70)
    return "Top-tier credit", "Prime doors already open", 1.0


def dominant_pressure_family(state: GameState) -> str:
    player = state.player
    if player.credit_score < 580:
        return "Credit pressure"
    if player.debt >= 18000:
        return "Debt pressure"
    if player.housing.housing_stability <= 42 or player.housing.missed_payment_streak > 0:
        return "Housing squeeze"
    if player.transport.reliability_score <= 45:
        return "Transport friction"
    if player.career.transition_penalty_months > 0 or player.career.layoff_pressure > 0:
        return "Career turbulence"
    if player.education.is_active and player.education.standing <= 55:
        return "Education pressure"
    if state.pending_user_choice_event_id or state.pending_events:
        return "Situation fallout"
    return "Steady month"


def _net_worth_score(state: GameState) -> float:
    return _clamp_score((net_worth(state) + 8000) / 500)


def _monthly_surplus_score(state: GameState) -> float:
    return _clamp_score((state.player.monthly_surplus + 1000) / 25)


def _debt_ratio_score(state: GameState) -> float:
    available_assets = max(
        1,
        state.player.cash
        + state.player.savings
        + state.player.high_interest_savings
        + state.player.index_fund
        + state.player.aggressive_growth_fund
        + 1000,
    )
    ratio = state.player.debt / available_assets
    credit_factor = (state.player.credit_score - 300) / 5.5
    return _clamp_score(100 - (ratio * 22) + (credit_factor * 0.3))


def _career_tier_score(bundle: ContentBundle, state: GameState) -> float:
    track = get_career_track(bundle, state.player.career.track_id)
    tier_share = 100 * ((state.player.career.tier_index + 1) / len(track.tiers))
    promotion_buffer = min(10, state.player.career.promotion_progress)
    seniority_buffer = min(5, state.player.career.months_at_tier // 3)
    streak_bonus = min(5, state.player.career.best_performance_streak)
    branch_bonus = 0
    if state.player.career.branch_id:
        branch_bonus = 3
        if state.player.career.tier_index >= 2:
            branch_bonus += 2
    return _clamp_score(tier_share + promotion_buffer + seniority_buffer + streak_bonus + branch_bonus)


def _credentials_score(state: GameState) -> float:
    completed = len(state.player.education.completed_program_ids)
    credentials = len(state.player.education.earned_credential_ids)
    gpa_bonus = max(0.0, (state.player.education.college_gpa - 2.0) * 10)
    pass_bonus = 10 if state.player.education.training_passed else 0
    grad_bonus = 0
    if state.player.education.graduation_tier == "distinguished":
        grad_bonus = 15
    elif state.player.education.graduation_tier == "strong":
        grad_bonus = 8
    elif state.player.education.graduation_tier == "basic":
        grad_bonus = -5
    return _clamp_score((completed * 18) + (credentials * 15) + gpa_bonus + pass_bonus + grad_bonus)


def _housing_score(bundle: ContentBundle, state: GameState) -> float:
    housing = get_housing_option(bundle, state.player.housing_id)
    penalty = state.player.housing.missed_payment_streak * 18
    stability_bonus = min(8, state.player.housing.months_in_place // 6)
    return _clamp_score(housing.quality_score - penalty + stability_bonus)


def _life_satisfaction_score(state: GameState) -> float:
    return _clamp_score((state.player.life_satisfaction * 0.7) + (state.player.social_stability * 0.3))


def _stress_burnout_score(state: GameState) -> float:
    stress_relief = 100 - state.player.stress
    energy = state.player.energy
    burnout_penalty = state.burnout_streak * 10
    liquidation_penalty = state.player.emergency_liquidation_count * 8
    return _clamp_score((stress_relief * 0.65) + (energy * 0.35) - burnout_penalty - liquidation_penalty)


def _consequence_pressure_penalty(state: GameState) -> float:
    player = state.player
    penalty = 0.0
    penalty += len(state.pending_events) * 2.6
    if state.pending_user_choice_event_id:
        penalty += 4.2
    penalty += player.housing.missed_payment_streak * 2.0
    penalty += player.emergency_liquidation_count * 1.7
    if player.monthly_surplus < 0:
        penalty += 1.2
    if player.credit_score < 580 and player.debt >= 7000:
        penalty += 1.5
    if player.transport.reliability_score < 45:
        penalty += 0.9
    return penalty


def _wealth_signature_score_adjustment(bundle: ContentBundle, state: GameState) -> float:
    player = state.player
    liquid = player.cash + player.savings + player.high_interest_savings
    invested = player.index_fund + player.aggressive_growth_fund
    strategy_id = player.wealth_strategy_id
    adjustment = 0.0

    if strategy_id == "cushion_first":
        if liquid >= max(bundle.config.emergency_fund_floor, 900) and player.emergency_liquidation_count == 0:
            adjustment += 1.6
        if liquid >= 3200 and player.debt >= 8500:
            adjustment -= 1.8
    elif strategy_id == "debt_crusher":
        if player.debt <= 3000 and player.monthly_surplus >= 0:
            adjustment += 2.2
        if player.debt >= 10000 and liquid < 600:
            adjustment -= 1.4
    elif strategy_id == "steady_builder":
        if liquid >= 900 and invested >= 3000 and player.debt <= 7000 and player.monthly_surplus >= 0:
            adjustment += 1.8
        if player.monthly_surplus < -100:
            adjustment -= 0.9
    elif strategy_id == "market_chaser":
        if invested >= 5000 and player.monthly_surplus >= 0 and player.credit_score >= 680:
            adjustment += 2.0
        if liquid > (invested * 2):
            adjustment -= 1.4
        if player.emergency_liquidation_count > 0:
            adjustment -= 2.2
        if player.monthly_surplus < 0 and player.debt >= 9000:
            adjustment -= 1.2

    return max(-4.0, min(4.0, adjustment))


def _biggest_risk_label(breakdown: dict[str, float], warnings: list[str]) -> str:
    if warnings:
        return warnings[0]

    weakest_key = min(breakdown, key=breakdown.get)
    weakest_value = breakdown[weakest_key]
    labels = {
        "net_worth": "Net worth is still the softest part of the run.",
        "monthly_surplus": "Cash flow is still the softest part of the run.",
        "debt_ratio": "Debt pressure is still the softest part of the run.",
        "career_tier": "Career momentum is still the softest part of the run.",
        "credentials_education": "Education progress is still the softest part of the run.",
        "housing_stability": "Housing stability is still the softest part of the run.",
        "life_satisfaction": "Life stability is still the softest part of the run.",
        "stress_burnout": "Stress and energy are still the softest part of the run.",
    }
    if weakest_value >= 75:
        return "No major crisis is pressing right now."
    return labels.get(weakest_key, "No major crisis is pressing right now.")


def _ending_label(bundle: ContentBundle, final_score: float, breakdown: dict[str, float], state: GameState) -> str:
    branch = _current_branch(bundle, state)
    if state.game_over_reason == "collections":
        return "Crushed by Bad Decisions" if state.player.debt > 32000 else "Educated but Overleveraged"
    if state.game_over_reason == "housing_loss":
        return "Crushed by Bad Decisions"
    if state.game_over_reason == "burnout_collapse":
        return "Burned-Out High Earner" if breakdown["net_worth"] >= 55 else "Burned-Out High Earner"
    if state.game_over_reason == "academic_collapse":
        return "Late Bloomer With Momentum" if final_score >= 55 else "Drifting Survivor"
    if branch is not None and final_score >= 58 and state.player.stress < 82:
        branch_labels = {
            "warehouse_dispatch_track": "Dispatch-Built Stabilizer",
            "warehouse_equipment_track": "Equipment Track Builder",
            "warehouse_ops_track": "Floor Operations Grinder",
            "retail_management_track": "Retail Operations Climber",
            "retail_sales_track": "Commission-Driven Climber",
            "retail_clienteling_track": "Client Book Builder",
        }
        branch_label = branch_labels.get(branch.id)
        if branch_label:
            return branch_label
    if final_score >= 82 and breakdown["life_satisfaction"] >= 55:
        return "Financially Secure Builder"
    if breakdown["credentials_education"] >= 62 and state.player.debt >= 18000:
        return "Educated but Overleveraged"
    if state.player.career.track_id == "trades_apprenticeship" and final_score >= 58:
        return "Stable Blue-Collar Grinder"
    if final_score >= 60 and state.player.social_stability >= 55:
        return "Late Bloomer With Momentum"
    if state.player.stress >= 82:
        return "Burned-Out High Earner"
    if final_score < 42:
        return "Crushed by Bad Decisions"
    return "Drifting Survivor"


def calculate_final_score(bundle: ContentBundle, state: GameState) -> FinalScoreSummary:
    weights = bundle.scoring_weights
    breakdown = {
        "net_worth": round(_net_worth_score(state), 2),
        "monthly_surplus": round(_monthly_surplus_score(state), 2),
        "debt_ratio": round(_debt_ratio_score(state), 2),
        "career_tier": round(_career_tier_score(bundle, state), 2),
        "credentials_education": round(_credentials_score(state), 2),
        "housing_stability": round(_housing_score(bundle, state), 2),
        "life_satisfaction": round(_life_satisfaction_score(state), 2),
        "stress_burnout": round(_stress_burnout_score(state), 2),
    }
    weighted_score = (
        (breakdown["net_worth"] * weights.net_worth)
        + (breakdown["monthly_surplus"] * weights.monthly_surplus)
        + (breakdown["debt_ratio"] * weights.debt_ratio)
        + (breakdown["career_tier"] * weights.career_tier)
        + (breakdown["credentials_education"] * weights.credentials_education)
        + (breakdown["housing_stability"] * weights.housing_stability)
        + (breakdown["life_satisfaction"] * weights.life_satisfaction)
        + (breakdown["stress_burnout"] * weights.stress_burnout)
    )
    wealth_adjustment = _wealth_signature_score_adjustment(bundle, state)
    final_score = round(_clamp_score(weighted_score + wealth_adjustment - _consequence_pressure_penalty(state)), 2)
    branch = _current_branch(bundle, state)
    run_identity = None
    if branch is not None:
        track = get_career_track(bundle, state.player.career.track_id)
        run_identity = f"{track.name} | {branch.name}"
    survived = state.game_over_reason is None and state.current_month > state.total_months
    if survived:
        if branch is not None:
            outcome = f"You reached age 28 and carved out a real life position through the {branch.name} branch."
        else:
            outcome = "You reached age 28 and carved out a real life position."
    elif state.game_over_reason == "collections":
        outcome = "Debt pressure broke the run before age 28."
    elif state.game_over_reason == "housing_loss":
        outcome = "Housing instability collapsed the run before you could recover."
    elif state.game_over_reason == "burnout_collapse":
        outcome = "Burnout hit hard enough to break the run early."
    elif state.game_over_reason == "academic_collapse":
        outcome = "School collapsed badly enough to close the run's main lane."
    else:
        outcome = "The run ended before you reached age 28."
    return FinalScoreSummary(
        final_score=final_score,
        survived_to_28=survived,
        outcome=outcome,
        ending_label=_ending_label(bundle, final_score, breakdown, state),
        run_identity=run_identity,
        breakdown=breakdown,
    )


def build_live_score_snapshot(
    bundle: ContentBundle,
    state: GameState,
    *,
    warnings: list[str] | None = None,
) -> LiveScoreSnapshot:
    summary = calculate_final_score(bundle, state)
    return LiveScoreSnapshot(
        projected_score=summary.final_score,
        score_tier=_score_tier_label(summary.final_score),
        biggest_risk=_biggest_risk_label(summary.breakdown, warnings or []),
        breakdown=summary.breakdown,
    )
