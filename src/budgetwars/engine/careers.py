from __future__ import annotations

from budgetwars.models import CareerTrackDefinition, ContentBundle, GameState

from .effects import append_log
from .lookups import get_career_track, get_city, get_current_career_tier, get_transport_option


def can_enter_career(bundle: ContentBundle, state: GameState, career_id: str) -> tuple[bool, str]:
    track = get_career_track(bundle, career_id)
    player = state.player
    transport = get_transport_option(bundle, player.transport_id)
    if career_id == player.career.track_id:
        return False, "You are already on that career track."
    if player.opening_path_id not in track.entry_path_ids:
        return False, "That track does not fit your starting path in this version."
    if transport.access_level < track.minimum_transport_access:
        return False, "Your current transport setup cannot support that work."
    if track.entry_requires_active_education and (
        not player.education.is_active or player.education.program_id != track.entry_required_education_program_id
    ):
        return False, "You need the matching active training program first."
    if track.entry_minimum_gpa is not None and player.education.college_gpa < track.entry_minimum_gpa:
        return False, f"You need at least a {track.entry_minimum_gpa:.1f} GPA for that track."
    missing = [credential for credential in track.entry_required_credential_ids if credential not in player.education.earned_credential_ids]
    if missing:
        return False, "You do not have the credential needed for that track yet."
    return True, ""


def current_income(bundle: ContentBundle, state: GameState, income_multiplier: float) -> int:
    city = get_city(bundle, state.player.current_city_id)
    tier = get_current_career_tier(bundle, state)
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)
    career_bias = city.career_income_biases.get(state.player.career.track_id, 1.0)
    income = tier.monthly_income * career_bias * difficulty.income_multiplier * income_multiplier
    return max(0, int(round(income)))


def apply_career_effects(bundle: ContentBundle, state: GameState) -> None:
    tier = get_current_career_tier(bundle, state)
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)
    state.player.energy += tier.energy_delta
    state.player.stress += int(round(tier.stress_delta * difficulty.stress_multiplier))
    state.player.life_satisfaction += tier.life_satisfaction_delta
    state.player.career.months_in_track += 1


def add_promotion_progress(bundle: ContentBundle, state: GameState, bonus: int) -> None:
    progress_gain = 1 + max(0, bonus)
    if state.player.energy >= 55:
        progress_gain += 1
    if state.player.stress >= 80:
        progress_gain -= 1
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)
    progress_gain = max(0, int(round(progress_gain * difficulty.progress_multiplier)))
    state.player.career.promotion_progress += progress_gain


def maybe_promote(bundle: ContentBundle, state: GameState) -> None:
    track = get_career_track(bundle, state.player.career.track_id)
    tier = track.tiers[state.player.career.tier_index]
    if state.player.career.tier_index >= len(track.tiers) - 1:
        return
    if state.player.career.promotion_progress < tier.promotion_target:
        return
    next_tier = track.tiers[state.player.career.tier_index + 1]
    missing = [credential for credential in next_tier.required_credential_ids if credential not in state.player.education.earned_credential_ids]
    if missing:
        return
    if next_tier.required_minimum_gpa is not None and state.player.education.college_gpa < next_tier.required_minimum_gpa:
        return
    state.player.career.tier_index += 1
    state.player.career.promotion_progress = 0
    append_log(state, f"You moved up to {next_tier.label} in {track.name}.")
