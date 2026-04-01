from __future__ import annotations

from budgetwars.models import ContentBundle, FinalScoreSummary, GameState

from .effects import net_worth
from .lookups import get_career_track, get_housing_option


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


def _net_worth_score(state: GameState) -> float:
    return _clamp_score((net_worth(state) + 8000) / 500)


def _monthly_surplus_score(state: GameState) -> float:
    return _clamp_score((state.player.monthly_surplus + 1000) / 25)


def _debt_ratio_score(state: GameState) -> float:
    available_assets = max(1, state.player.cash + state.player.savings + 1000)
    ratio = state.player.debt / available_assets
    return _clamp_score(100 - (ratio * 22))


def _career_tier_score(bundle: ContentBundle, state: GameState) -> float:
    track = get_career_track(bundle, state.player.career.track_id)
    tier_share = 100 * ((state.player.career.tier_index + 1) / len(track.tiers))
    promotion_buffer = min(10, state.player.career.promotion_progress)
    return _clamp_score(tier_share + promotion_buffer)


def _credentials_score(state: GameState) -> float:
    completed = len(state.player.education.completed_program_ids)
    credentials = len(state.player.education.earned_credential_ids)
    gpa_bonus = max(0.0, (state.player.education.college_gpa - 2.0) * 10)
    pass_bonus = 10 if state.player.education.training_passed else 0
    return _clamp_score((completed * 18) + (credentials * 15) + gpa_bonus + pass_bonus)


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
    return _clamp_score((stress_relief * 0.65) + (energy * 0.35) - burnout_penalty)


def _ending_label(final_score: float, breakdown: dict[str, float], state: GameState) -> str:
    if state.game_over_reason == "collections":
        return "Crushed by Bad Decisions" if state.player.debt > 32000 else "Educated but Overleveraged"
    if state.game_over_reason == "housing_loss":
        return "Crushed by Bad Decisions"
    if state.game_over_reason == "burnout_collapse":
        return "Burned-Out High Earner" if breakdown["net_worth"] >= 55 else "Burned-Out High Earner"
    if state.game_over_reason == "academic_collapse":
        return "Late Bloomer With Momentum" if final_score >= 55 else "Drifting Survivor"
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
    final_score = round(
        (breakdown["net_worth"] * weights.net_worth)
        + (breakdown["monthly_surplus"] * weights.monthly_surplus)
        + (breakdown["debt_ratio"] * weights.debt_ratio)
        + (breakdown["career_tier"] * weights.career_tier)
        + (breakdown["credentials_education"] * weights.credentials_education)
        + (breakdown["housing_stability"] * weights.housing_stability)
        + (breakdown["life_satisfaction"] * weights.life_satisfaction)
        + (breakdown["stress_burnout"] * weights.stress_burnout),
        2,
    )
    survived = state.game_over_reason is None and state.current_month > state.total_months
    if survived:
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
        ending_label=_ending_label(final_score, breakdown, state),
        breakdown=breakdown,
    )
