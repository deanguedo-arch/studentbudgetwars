from __future__ import annotations

from budgetwars.models import ContentBundle, FinalScoreSummary, GameState

from .effects import net_worth
from .lookups import get_career_track, get_current_career_tier, get_housing_option


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


def _financial_score(state: GameState) -> float:
    worth = net_worth(state)
    worth_component = _clamp_score((worth + 5000) / 350)
    surplus_component = _clamp_score((state.player.monthly_surplus + 600) / 18)
    return (worth_component * 0.7) + (surplus_component * 0.3)


def _career_score(bundle: ContentBundle, state: GameState) -> float:
    track = get_career_track(bundle, state.player.career.track_id)
    tier_share = 100 * ((state.player.career.tier_index + 1) / len(track.tiers))
    credential_bonus = min(25, len(state.player.education.earned_credential_ids) * 12.5)
    promotion_buffer = min(10, state.player.career.promotion_progress)
    return _clamp_score(tier_share * 0.7 + credential_bonus + promotion_buffer)


def _housing_score(bundle: ContentBundle, state: GameState) -> float:
    housing = get_housing_option(bundle, state.player.housing_id)
    penalty = state.missed_housing_payments * 12
    return _clamp_score(housing.quality_score - penalty)


def _debt_score(state: GameState) -> float:
    return _clamp_score(100 - (state.player.debt / 600))


def _wellbeing_score(state: GameState) -> float:
    satisfaction = state.player.life_satisfaction * 0.45
    energy = state.player.energy * 0.25
    stress_relief = (100 - state.player.stress) * 0.30
    return _clamp_score(satisfaction + energy + stress_relief)


def _ending_label(final_score: float, state: GameState) -> str:
    if state.game_over_reason == "burnout_collapse":
        return "Burned-Out Striver"
    if state.game_over_reason == "collections":
        return "Overleveraged Achiever"
    if final_score >= 80:
        return "Financially Secure Builder"
    if final_score >= 62:
        return "Stable Grinder"
    if final_score >= 46:
        return "Overleveraged Achiever" if state.player.debt > 18000 else "Stable Grinder"
    if state.player.stress > 82:
        return "Burned-Out Striver"
    return "Drifting Survivor"


def calculate_final_score(bundle: ContentBundle, state: GameState) -> FinalScoreSummary:
    weights = bundle.scoring_weights
    breakdown = {
        "financial_position": round(_financial_score(state), 2),
        "career_and_credentials": round(_career_score(bundle, state), 2),
        "housing_stability": round(_housing_score(bundle, state), 2),
        "debt_burden": round(_debt_score(state), 2),
        "wellbeing": round(_wellbeing_score(state), 2),
    }
    final_score = round(
        (breakdown["financial_position"] * weights.financial_position)
        + (breakdown["career_and_credentials"] * weights.career_and_credentials)
        + (breakdown["housing_stability"] * weights.housing_stability)
        + (breakdown["debt_burden"] * weights.debt_burden)
        + (breakdown["wellbeing"] * weights.wellbeing),
        2,
    )
    survived = state.game_over_reason is None and state.current_month > state.total_months
    if survived:
        outcome = "You reached age 28 and built a real position."
    elif state.game_over_reason == "collections":
        outcome = "Debt collectors closed the run before age 28."
    elif state.game_over_reason == "housing_loss":
        outcome = "Housing instability knocked the run out early."
    elif state.game_over_reason == "burnout_collapse":
        outcome = "Burnout collapsed the run before you could stabilize it."
    else:
        outcome = "The run ended before you reached age 28."
    return FinalScoreSummary(
        final_score=final_score,
        survived_to_28=survived,
        outcome=outcome,
        ending_label=_ending_label(final_score, state),
        breakdown=breakdown,
    )
