from __future__ import annotations

from random import Random

from budgetwars.models import ContentBundle, GameState
from budgetwars.utils.rng import derive_seed

from .effects import append_log
from .lookups import get_career_track, get_city, get_current_career_tier, get_transport_option


def can_enter_career(bundle: ContentBundle, state: GameState, career_id: str) -> tuple[bool, str]:
    track = get_career_track(bundle, career_id)
    player = state.player
    transport = get_transport_option(bundle, player.transport_id)
    if career_id == player.career.track_id:
        return False, "You are already on that career track."
    if player.opening_path_id not in track.entry_path_ids:
        return False, "That track is not available from your current life lane."
    if transport.access_level < track.minimum_transport_access:
        return False, "Your current transport setup cannot support that work."
    if track.entry_requires_active_education and (
        not player.education.is_active or player.education.program_id != track.entry_required_education_program_id
    ):
        return False, "You need the matching active training program first."
    if track.entry_minimum_gpa is not None and player.education.college_gpa < track.entry_minimum_gpa:
        return False, f"You need at least a {track.entry_minimum_gpa:.1f} GPA for that track."
    if track.entry_requires_pass_state and not player.education.training_passed:
        return False, "You need to pass training before that lane opens."
    missing = [credential for credential in track.entry_required_credential_ids if credential not in player.education.earned_credential_ids]
    if missing:
        return False, "You do not have the credential needed for that track yet."
    if career_id in {"warehouse_logistics", "trades_apprenticeship"} and player.transport.reliability_score < 45:
        return False, "That lane needs steadier transport reliability than you currently have."
    if career_id == "sales" and player.social_stability < 35:
        return False, "Your social stability is too low to hold a sales lane right now."
    if career_id == "degree_gated_professional" and player.education.college_gpa < 3.0:
        return False, "That lane requires college momentum and a stronger GPA baseline."
    return True, ""


def _income_variance_factor(state: GameState, variance: float) -> float:
    if variance <= 0:
        return 1.0
    rng = Random(derive_seed(state.seed, state.current_month, state.player.career.track_id, "income"))
    return 1.0 + rng.uniform(-variance, variance)


def current_income(bundle: ContentBundle, state: GameState, income_multiplier: float) -> int:
    city = get_city(bundle, state.player.current_city_id)
    tier = get_current_career_tier(bundle, state)
    track = get_career_track(bundle, state.player.career.track_id)
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)
    career_bias = city.career_income_biases.get(state.player.career.track_id, 1.0)
    social_bonus = 1.0 + (track.social_income_factor * max(0, state.player.social_stability - 50))
    variance = _income_variance_factor(state, track.income_variance)
    transition_drag = 0.82 if state.player.career.transition_penalty_months > 0 else 1.0
    momentum_multiplier = 1.0 + ((state.player.career.promotion_momentum - 50) * 0.003)
    seniority_bonus = (state.player.career.months_at_tier // 6) * tier.seniority_income_bonus
    # Energy cap: exhausted workers cannot sustain overtime or gig-economy hours
    if state.player.energy < 30:
        energy_cap = 0.6 if track.income_variance > 0 or track.id in {"delivery_gig", "warehouse_logistics"} else 0.8
    else:
        energy_cap = 1.0
    income = (
        (tier.monthly_income + seniority_bonus)
        * career_bias
        * difficulty.income_multiplier
        * income_multiplier
        * social_bonus
        * variance
        * transition_drag
        * momentum_multiplier
        * energy_cap
    )
    return max(0, int(round(income)))


def apply_career_effects(bundle: ContentBundle, state: GameState) -> None:
    tier = get_current_career_tier(bundle, state)
    track = get_career_track(bundle, state.player.career.track_id)
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)
    state.player.energy += tier.energy_delta
    state.player.stress += int(round(tier.stress_delta * difficulty.stress_multiplier))
    state.player.life_satisfaction += tier.life_satisfaction_delta
    state.player.social_stability += tier.social_stability_delta
    state.player.career.months_in_track += 1
    state.player.career.months_at_tier += 1
    if state.player.career.transition_penalty_months > 0:
        state.player.career.transition_penalty_months -= 1
        state.player.stress += 2
        state.player.energy -= 2
    if state.player.stress >= 80 or state.player.energy <= 25:
        state.player.career.promotion_momentum = max(0, state.player.career.promotion_momentum - 3)
    elif state.player.energy >= 60 and state.player.stress <= 65:
        state.player.career.promotion_momentum = min(100, state.player.career.promotion_momentum + 2)
    if track.id == "sales":
        if state.player.social_stability >= 65:
            state.player.career.promotion_momentum = min(100, state.player.career.promotion_momentum + 2)
        if state.player.stress >= 82:
            state.player.career.promotion_momentum = max(0, state.player.career.promotion_momentum - 4)
    if track.id in {"warehouse_logistics", "trades_apprenticeship"} and state.player.transport.reliability_score <= 50:
        state.player.career.promotion_momentum = max(0, state.player.career.promotion_momentum - 2)
    if state.player.housing.housing_stability <= 42:
        state.player.career.promotion_momentum = max(0, state.player.career.promotion_momentum - 1)
    if state.player.career.promotion_momentum >= 70:
        state.player.career.recent_performance_tag = "uptrend"
        state.player.career.best_performance_streak += 1
    elif state.player.career.promotion_momentum <= 30:
        state.player.career.recent_performance_tag = "downtrend"
        state.player.career.best_performance_streak = 0
    else:
        state.player.career.recent_performance_tag = "steady"
        state.player.career.best_performance_streak = 0
    if track.layoff_weight > 1.0:
        state.player.career.layoff_pressure += 1
    elif state.player.career.layoff_pressure > 0:
        state.player.career.layoff_pressure -= 1


def add_promotion_progress(bundle: ContentBundle, state: GameState, bonus: int) -> None:
    track = get_career_track(bundle, state.player.career.track_id)
    progress_gain = 1 + max(0, bonus)
    if state.player.career.recent_performance_tag == "uptrend":
        progress_gain += 1
    elif state.player.career.recent_performance_tag == "downtrend":
        progress_gain -= 1
    if state.player.energy >= 55:
        progress_gain += 1
    if state.player.stress >= 80:
        progress_gain -= 1
    if state.player.social_stability >= 60 and track.social_income_factor > 0:
        progress_gain += 1
    if state.player.career.promotion_momentum >= 68:
        progress_gain += 1
    if state.player.career.promotion_momentum <= 30:
        progress_gain -= 1
    if state.player.career.transition_penalty_months > 0:
        progress_gain -= 1
    if track.id == "delivery_gig" and state.player.transport.reliability_score < 55:
        progress_gain -= 1
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)
    progress_gain = max(0, int(round(progress_gain * difficulty.progress_multiplier * track.promotion_weight)))
    state.player.career.promotion_progress += progress_gain


def promotion_blockers(bundle: ContentBundle, state: GameState) -> list[str]:
    track = get_career_track(bundle, state.player.career.track_id)
    tier = track.tiers[state.player.career.tier_index]
    if state.player.career.tier_index >= len(track.tiers) - 1:
        return []
    next_tier = track.tiers[state.player.career.tier_index + 1]
    blockers: list[str] = []
    if state.player.career.promotion_progress < tier.promotion_target:
        blockers.append(f"Needs {tier.promotion_target} progress ({state.player.career.promotion_progress} now).")
    missing = [credential for credential in next_tier.required_credential_ids if credential not in state.player.education.earned_credential_ids]
    if missing:
        blockers.append(f"Missing credential: {', '.join(missing)}.")
    if next_tier.required_minimum_gpa is not None and state.player.education.college_gpa < next_tier.required_minimum_gpa:
        blockers.append(f"GPA {next_tier.required_minimum_gpa:.1f}+ required.")
    if next_tier.required_pass_state and not state.player.education.training_passed:
        blockers.append("Training pass-state required.")
    if track.id == "retail_service" and state.player.housing.housing_stability < 45:
        blockers.append("Housing instability is slowing reliability-based promotion.")
    if track.id == "warehouse_logistics" and state.player.energy < 28:
        blockers.append("Energy is too low for warehouse leadership progression.")
    if track.id == "delivery_gig" and state.player.transport.reliability_score < 55:
        blockers.append("Delivery progression needs steadier transport reliability.")
    if track.id == "office_admin" and state.player.social_stability < 45:
        blockers.append("Office progression needs stronger social consistency.")
    if track.id == "trades_apprenticeship" and state.player.transport.reliability_score < 60:
        blockers.append("Trades progression needs reliable transport access.")
    if track.id == "healthcare_support" and state.player.stress >= 86:
        blockers.append("Stress is too high for higher-responsibility care roles.")
    if track.id == "sales" and state.player.career.promotion_momentum < 55:
        blockers.append("Sales promotion needs stronger momentum.")
    if track.id == "degree_gated_professional" and not state.player.education.earned_credential_ids:
        blockers.append("Professional track progression depends on completed credentials.")
    return blockers


def maybe_promote(bundle: ContentBundle, state: GameState) -> None:
    track = get_career_track(bundle, state.player.career.track_id)
    if state.player.career.tier_index >= len(track.tiers) - 1:
        return
    if promotion_blockers(bundle, state):
        return
    next_tier = track.tiers[state.player.career.tier_index + 1]
    state.player.career.tier_index += 1
    state.player.career.promotion_progress = 0
    state.player.career.months_at_tier = 0
    state.player.career.promotion_momentum = min(100, state.player.career.promotion_momentum + 7)
    append_log(state, f"You moved up to {next_tier.label} in {track.name}.")
