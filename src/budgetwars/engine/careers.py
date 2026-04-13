from __future__ import annotations

from random import Random

from budgetwars.models import CareerBranchDefinition, ContentBundle, GameState
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


def _current_branch(bundle: ContentBundle, state: GameState) -> CareerBranchDefinition | None:
    branch_id = state.player.career.branch_id
    if not branch_id:
        return None
    track = get_career_track(bundle, state.player.career.track_id)
    return next((branch for branch in track.branches if branch.id == branch_id), None)


def branch_options(bundle: ContentBundle, state: GameState) -> list[CareerBranchDefinition]:
    track = get_career_track(bundle, state.player.career.track_id)
    return list(track.branches)


def can_select_branch(bundle: ContentBundle, state: GameState, branch_id: str) -> tuple[bool, str]:
    track = get_career_track(bundle, state.player.career.track_id)
    branch = next((item for item in track.branches if item.id == branch_id), None)
    if branch is None:
        return False, "That branch does not exist for your current career track."
    player = state.player
    if player.career.tier_index < branch.min_tier_index:
        return False, f"You need to reach tier {branch.min_tier_index + 1} before that branch opens."
    if branch.min_transport_reliability is not None and player.transport.reliability_score < branch.min_transport_reliability:
        return False, "Transport reliability is too low for that branch."
    if branch.min_social_stability is not None and player.social_stability < branch.min_social_stability:
        return False, "Social stability is too low for that branch."
    if branch.min_energy is not None and player.energy < branch.min_energy:
        return False, "Energy is too low for that branch."
    if branch.max_stress is not None and player.stress > branch.max_stress:
        return False, "Stress is too high for that branch."
    missing = [credential for credential in branch.required_credential_ids if credential not in player.education.earned_credential_ids]
    if missing:
        return False, f"Missing credential: {', '.join(missing)}."
    return True, ""


def branch_statuses(bundle: ContentBundle, state: GameState) -> list[tuple[CareerBranchDefinition, bool, str]]:
    statuses: list[tuple[CareerBranchDefinition, bool, str]] = []
    for branch in branch_options(bundle, state):
        allowed, reason = can_select_branch(bundle, state, branch.id)
        statuses.append((branch, allowed, reason))
    return statuses


def _income_variance_factor(state: GameState, variance: float) -> float:
    if variance <= 0:
        return 1.0
    rng = Random(derive_seed(state.seed, state.current_month, state.player.career.track_id, "income"))
    return 1.0 + rng.uniform(-variance, variance)


def current_income(bundle: ContentBundle, state: GameState, income_multiplier: float) -> int:
    city = get_city(bundle, state.player.current_city_id)
    tier = get_current_career_tier(bundle, state)
    track = get_career_track(bundle, state.player.career.track_id)
    branch = _current_branch(bundle, state)
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
    if branch is not None:
        income *= branch.income_multiplier
    return max(0, int(round(income)))


def _apply_branch_identity_momentum(state: GameState, track_id: str, branch_id: str | None) -> None:
    if not branch_id:
        return
    player = state.player
    career = player.career
    if track_id == "retail_service":
        if branch_id == "retail_management_track":
            if player.stress >= 74:
                career.promotion_momentum = max(0, career.promotion_momentum - 2)
                career.layoff_pressure += 1
            if player.social_stability >= 62 and player.housing.housing_stability >= 55:
                career.promotion_momentum = min(100, career.promotion_momentum + 1)
        elif branch_id == "retail_sales_track":
            if player.social_stability >= 66 and player.energy >= 45:
                career.promotion_momentum = min(100, career.promotion_momentum + 2)
            if player.social_stability < 55:
                career.promotion_momentum = max(0, career.promotion_momentum - 2)
            if player.stress >= 78:
                career.promotion_momentum = max(0, career.promotion_momentum - 1)
        elif branch_id == "retail_clienteling_track":
            if player.social_stability >= 68 and player.stress <= 64:
                career.promotion_momentum = min(100, career.promotion_momentum + 3)
            if player.social_stability <= 58 or player.housing.housing_stability < 50:
                career.promotion_momentum = max(0, career.promotion_momentum - 3)
                career.layoff_pressure += 1
    if track_id == "warehouse_logistics":
        if branch_id == "warehouse_ops_track":
            if player.energy <= 38:
                career.promotion_momentum = max(0, career.promotion_momentum - 3)
                career.layoff_pressure += 1
            if player.transport.reliability_score >= 70 and player.energy >= 50:
                career.promotion_momentum = min(100, career.promotion_momentum + 1)
        elif branch_id == "warehouse_dispatch_track":
            if player.social_stability >= 58 and player.transport.reliability_score >= 68:
                career.promotion_momentum = min(100, career.promotion_momentum + 2)
            if player.social_stability < 48 or player.transport.reliability_score < 58:
                career.promotion_momentum = max(0, career.promotion_momentum - 2)
        elif branch_id == "warehouse_equipment_track":
            if player.transport.reliability_score >= 72 and player.energy >= 48:
                career.promotion_momentum = min(100, career.promotion_momentum + 2)
            if player.transport.reliability_score < 66 or player.stress >= 72:
                career.promotion_momentum = max(0, career.promotion_momentum - 3)
                career.layoff_pressure += 1


def _branch_specific_promotion_blockers(state: GameState, track_id: str, branch_id: str | None) -> list[str]:
    if not branch_id:
        return []
    player = state.player
    tags = set(player.persistent_tags)
    blockers: list[str] = []
    if track_id == "retail_service":
        if branch_id == "retail_management_track" and player.stress >= 74:
            blockers.append("Management branch promotion is blocked by high stress.")
        if branch_id == "retail_management_track":
            if "retail_management_crisis_lead_lane" in tags and player.stress >= 72:
                blockers.append("Crisis-lead lane requires stress to settle before another promotion push.")
            if "retail_management_output_surge_lane" in tags and player.energy < 42:
                blockers.append("Output-surge lane needs more energy buffer for the next promotion step.")
            if "retail_management_sustainable_ops_lane" in tags and player.social_stability < 58:
                blockers.append("Sustainable-ops lane promotion depends on stronger team consistency.")
        if branch_id == "retail_sales_track" and player.social_stability < 58:
            blockers.append("Sales branch promotion needs stronger social consistency.")
        if branch_id == "retail_clienteling_track":
            if player.social_stability < 64:
                blockers.append("Clienteling branch promotion needs stronger social consistency.")
            if player.housing.housing_stability < 50:
                blockers.append("Clienteling branch promotion needs steadier housing consistency.")
    if track_id == "warehouse_logistics":
        if branch_id == "warehouse_ops_track" and player.energy < 40:
            blockers.append("Warehouse ops promotion needs more physical energy buffer.")
        if branch_id == "warehouse_dispatch_track":
            if player.social_stability < 50:
                blockers.append("Warehouse dispatch promotion needs stronger coordination consistency.")
            if player.transport.reliability_score < 60:
                blockers.append("Warehouse dispatch promotion needs steadier transport reliability.")
            if "dispatch_escalation_lane" in tags and player.transport.reliability_score < 66:
                blockers.append("Escalation dispatch lane needs higher transport reliability to keep advancing.")
            if "dispatch_experiment_lane" in tags and player.social_stability < 55:
                blockers.append("Experiment dispatch lane promotion needs stronger social consistency.")
            if "dispatch_resilience_lane" in tags and player.energy < 34:
                blockers.append("Resilience dispatch lane promotion needs enough energy reserve.")
        if branch_id == "warehouse_equipment_track" and player.transport.reliability_score < 68:
            blockers.append("Warehouse equipment promotion needs higher transport reliability.")
    return blockers


def apply_career_effects(bundle: ContentBundle, state: GameState) -> None:
    tier = get_current_career_tier(bundle, state)
    track = get_career_track(bundle, state.player.career.track_id)
    branch = _current_branch(bundle, state)
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)
    state.player.energy += tier.energy_delta
    state.player.stress += int(round(tier.stress_delta * difficulty.stress_multiplier))
    if branch is not None:
        state.player.energy += branch.energy_delta
        state.player.stress += branch.stress_delta
        state.player.career.layoff_pressure = max(0, state.player.career.layoff_pressure + branch.layoff_pressure_delta)
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
    _apply_branch_identity_momentum(state, track.id, state.player.career.branch_id)
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
    branch = _current_branch(bundle, state)
    progress_gain = 1 + max(0, bonus)
    if branch is not None:
        progress_gain += branch.promotion_progress_bonus
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
    branch = _current_branch(bundle, state)
    if branch is not None:
        if branch.min_transport_reliability is not None and state.player.transport.reliability_score < branch.min_transport_reliability:
            blockers.append("Current branch needs higher transport reliability.")
        if branch.max_stress is not None and state.player.stress > branch.max_stress:
            blockers.append("Current branch is straining under current stress.")
    blockers.extend(_branch_specific_promotion_blockers(state, track.id, state.player.career.branch_id))
    return blockers


def maybe_promote(bundle: ContentBundle, state: GameState) -> None:
    track = get_career_track(bundle, state.player.career.track_id)
    if state.player.career.tier_index >= len(track.tiers) - 1:
        return
    if promotion_blockers(bundle, state):
        return
    if track.branches:
        min_branch_tier = min(branch.min_tier_index for branch in track.branches)
        if state.player.career.tier_index >= min_branch_tier and not state.player.career.branch_id:
            if state.pending_promotion_branch_track_id != track.id:
                append_log(state, f"Promotion decision pending: choose a branch in {track.name} before advancing.")
            state.pending_promotion_branch_track_id = track.id
            return
    next_tier = track.tiers[state.player.career.tier_index + 1]
    state.player.career.tier_index += 1
    state.player.career.promotion_progress = 0
    state.player.career.months_at_tier = 0
    state.player.career.promotion_momentum = min(100, state.player.career.promotion_momentum + 7)
    state.pending_promotion_branch_track_id = None
    append_log(state, f"You moved up to {next_tier.label} in {track.name}.")
