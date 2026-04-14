from __future__ import annotations

from budgetwars.engine.careers import current_role_band_label

from .choice_previews import _money
from .view_builders import (
    _current_focus_description,
    _current_focus_name,
    _format_persistent_commitments,
    _resolve_context,
)
from .view_models import BuildSnapshotVM, BuildSystemVM


def build_build_snapshot_vm(source, bundle=None) -> BuildSnapshotVM:
    controller = _resolve_context(source, bundle)
    state = controller.state
    player = state.player
    city = next(item for item in controller.bundle.cities if item.id == player.current_city_id)
    career_track = next(track for track in controller.bundle.careers if track.id == player.career.track_id)
    current_tier = career_track.tiers[player.career.tier_index]
    education = next(program for program in controller.bundle.education_programs if program.id == player.education.program_id)
    housing = next(item for item in controller.bundle.housing_options if item.id == player.housing_id)
    transport = next(item for item in controller.bundle.transport_options if item.id == player.transport_id)
    wealth = next(item for item in controller.bundle.wealth_strategies if item.id == player.wealth_strategy_id)
    focus = next(item for item in controller.bundle.focus_actions if item.id == player.selected_focus_action_id)
    branch = next((item for item in career_track.branches if item.id == player.career.branch_id), None)
    role_band_label = current_role_band_label(state)
    focus_name = _current_focus_name(controller)
    career_progress = f"Progress: {player.career.promotion_progress}/{career_track.tiers[player.career.tier_index].promotion_target}"
    if player.career.tier_index >= len(career_track.tiers) - 1:
        if role_band_label:
            career_progress = (
                f"Late-career: {role_band_label} L{player.career.post_cap_advancement_level} | "
                f"momentum {player.career.promotion_momentum}"
            )
        else:
            career_progress = f"Progress: max tier reached | momentum {player.career.promotion_momentum}"
    education_progress = (
        f"Progress: {player.education.months_completed}/{next((program.duration_months for program in controller.bundle.education_programs if program.id == player.education.program_id), 0)} months"
        if player.education.is_active and player.education.program_id != "none"
        else f"Progress: standing {player.education.standing}/100"
    )
    systems = [
        BuildSystemVM(
            "Career",
            current_tier.label,
            (
                f"{career_track.name} | {branch.name} | momentum {player.career.promotion_momentum}"
                if branch is not None
                else f"{career_track.name} | open branch lane | momentum {player.career.promotion_momentum}"
            ),
            career_progress,
            "career",
        ),
        BuildSystemVM(
            "Education",
            education.name,
            f"{'Active' if player.education.is_active else 'Paused'} | {player.education.intensity_level.title()}",
            education_progress,
            "education",
        ),
        BuildSystemVM(
            "Housing",
            housing.name,
            f"{player.housing.housing_stability}/100 stability",
            f"Progress: {player.housing.months_in_place} months in place",
            "housing",
        ),
        BuildSystemVM(
            "Transport",
            transport.name,
            f"{player.transport.reliability_score}/100 reliability",
            f"Progress: {player.transport.months_owned} months owned",
            "transport",
        ),
        BuildSystemVM(
            "Wealth",
            wealth.name,
            f"Portfolio: {_money(player.high_interest_savings + player.index_fund + player.aggressive_growth_fund)}",
            f"Progress: wealth buffer {_money(player.high_interest_savings + player.index_fund + player.aggressive_growth_fund)}",
            "wealth",
        ),
        BuildSystemVM(
            "Focus",
            focus_name,
            _current_focus_description(controller),
            f"Progress: {focus.income_multiplier:.2f}x income | {focus.promotion_progress_bonus:+d} promo",
            "focus",
        ),
    ]
    identity_parts = [career_track.name, branch.name if branch is not None else "Uncommitted lane"]
    if role_band_label:
        identity_parts.append(role_band_label)
    identity_parts.append(wealth.name)
    identity_line = " | ".join(identity_parts)
    commitments = _format_persistent_commitments(player.persistent_tags)
    return BuildSnapshotVM(
        player_name=player.name,
        city_name=city.name,
        identity_line=identity_line,
        persistent_commitments=commitments,
        items=systems,
    )


def build_build_snapshot(source, bundle=None) -> BuildSnapshotVM:
    return build_build_snapshot_vm(source, bundle)
