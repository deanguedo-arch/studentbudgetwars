from __future__ import annotations

from budgetwars.engine.scoring import (
    build_live_score_snapshot,
    credit_progress_summary,
    credit_tier_label,
    dominant_pressure_family,
)

from .diagnostics import _pressure_map_lines, _score_progress_text
from .view_builders import _resolve_context
from .view_models import LearnDrawerVM, LearnTopicVM


def build_learn_drawer_vm(source, bundle=None) -> LearnDrawerVM:
    controller = _resolve_context(source, bundle)
    state = controller.state
    player = state.player
    pressure_family = dominant_pressure_family(state)
    credit_tier = credit_tier_label(player.credit_score)
    credit_progress_label, credit_progress_detail, _ = credit_progress_summary(player.credit_score)
    stress_line = f"Stress {player.stress}/{state.max_stress} | Energy {player.energy}/{state.max_energy}"
    snapshot = build_live_score_snapshot(controller.bundle, state)
    career_track = next(track for track in controller.bundle.careers if track.id == player.career.track_id)
    current_tier = career_track.tiers[player.career.tier_index]
    housing = next(item for item in controller.bundle.housing_options if item.id == player.housing_id)
    transport = next(item for item in controller.bundle.transport_options if item.id == player.transport_id)
    education = next(program for program in controller.bundle.education_programs if program.id == player.education.program_id)
    focus = next(item for item in controller.bundle.focus_actions if item.id == player.selected_focus_action_id)
    score_label, score_detail = _score_progress_text(snapshot.projected_score)

    pressure_sources: list[str] = []
    pressure_sources.extend(_pressure_map_lines(state, controller.bundle))
    pressure_sources.append(f"Biggest risk: {snapshot.biggest_risk}")
    if not pressure_sources:
        pressure_sources.append("No single pressure source is dominating right now.")

    topics = [
        LearnTopicVM(
            id="credit",
            title="Credit",
            what_it_is=f"You are at {player.credit_score} ({credit_tier}). {credit_progress_label}: {credit_progress_detail}.",
            how_to_raise=[
                "Keep monthly swing positive so the run is not leaning on emergency debt.",
                "Pay debt down before it starts controlling your access.",
                "Avoid chained crisis months that force missed payments or new borrowing.",
            ],
            how_to_lower=[
                "Let debt grow while cash flow stays weak.",
                "Take repeated crisis hits that make the month unstable.",
            ],
            why_it_matters=[
                "Credit changes which housing and transport doors stay open.",
                "High credit creates refinance and recovery options later in the run.",
            ],
            common_drivers=["debt", "cash flow", "emergency borrowing", "credit events"],
            related_situation_families=["credit", "housing", "transport"],
        ),
        LearnTopicVM(
            id="stress",
            title="Stress",
            what_it_is=f"Stress is {player.stress}/{state.max_stress}. It is the running pressure load on the build, not the same thing as burnout.",
            how_to_raise=[
                "Use recovery focus and stop stacking school pressure with aggressive work focus.",
                "Protect housing stability and transport reliability so small problems do not keep leaking into the month.",
            ],
            how_to_lower=[
                "Overtime, transition drag, bad housing months, and transport failures all push stress upward.",
                "Low energy makes high stress harder to shake and closer to burnout.",
            ],
            why_it_matters=[
                "Stress is the pressure bar. Burnout is what happens when high stress sticks with low energy.",
                "High stress cuts consistency and can collapse school or work momentum.",
            ],
            common_drivers=["focus choice", "housing stability", "transport friction", "education load", "debt pressure"],
            related_situation_families=["burnout", "housing", "transport", "education", "career"],
        ),
        LearnTopicVM(
            id="career",
            title="Career Momentum",
            what_it_is=f"You are {current_tier.label} in {career_track.name} with {player.career.promotion_momentum} momentum.",
            how_to_raise=[
                f"Use focus lines like {focus.name} when your recovery can support it.",
                "Keep transport reliable enough to show up consistently.",
                "Protect recovery so promotion progress can compound instead of stalling.",
            ],
            how_to_lower=[
                "Career switches, transition drag, and weak recovery slow promotion progress.",
                "Missing access requirements can cap how far the current lane can go.",
            ],
            why_it_matters=["Momentum drives promotions, income growth, and the score ceiling of the run."],
            common_drivers=["focus choice", "transport access", "stress", "transition drag"],
            related_situation_families=["career", "transport"],
        ),
        LearnTopicVM(
            id="housing",
            title="Housing Stability",
            what_it_is=f"You are in {housing.name} at {player.housing.housing_stability}/100 housing stability.",
            how_to_raise=[
                "Keep the rent paid and maintain enough buffer to absorb bad months.",
                "Move only when the new housing improves recovery or lowers pressure enough to matter.",
            ],
            how_to_lower=[
                "Missed payments and weak buffer turn housing into a pressure engine.",
                "Instability leaks into stress and can make the whole run feel shaky.",
            ],
            why_it_matters=["Housing stability changes recovery, monthly stress relief, and event pressure."],
            common_drivers=["rent pressure", "missed payments", "cash buffer", "family support"],
            related_situation_families=["housing", "family"],
        ),
        LearnTopicVM(
            id="transport",
            title="Transport Reliability",
            what_it_is=f"You are using {transport.name} at {player.transport.reliability_score}/100 reliability.",
            how_to_raise=[
                "Keep enough buffer for repairs or move into a more reliable option when access matters.",
                "Use credit and savings to escape transport traps instead of waiting for a collapse.",
            ],
            how_to_lower=[
                "Breakdown pressure and weak cash reserves turn transport into missed-work risk.",
                "Low credit can block stronger transport options when you need them most.",
            ],
            why_it_matters=["Transport controls work consistency and some career ceilings."],
            common_drivers=["reliability", "breakdown pressure", "credit", "cash buffer"],
            related_situation_families=["transport", "career", "credit"],
        ),
        LearnTopicVM(
            id="education",
            title="Education Standing",
            what_it_is=f"You are in {education.name} with standing {player.education.standing}/100.",
            how_to_raise=[
                "Pick an intensity you can actually support with cash, time, and energy.",
                "Keep stress manageable enough that school progress can hold instead of sliding.",
            ],
            how_to_lower=[
                "Overwork, re-entry drag, and repeated shaky months make school slip.",
                "Education suffers when you try to solve every money problem by grinding harder.",
            ],
            why_it_matters=["Education opens later careers and raises long-run score upside."],
            common_drivers=["intensity", "stress", "energy", "re-entry drag"],
            related_situation_families=["education", "career"],
        ),
        LearnTopicVM(
            id="score",
            title="Score Pace",
            what_it_is=f"Projected score is {snapshot.projected_score:.1f} ({snapshot.score_tier}). {score_label}: {score_detail}.",
            how_to_raise=[
                "Stabilize the weakest category first, then push your strongest lane.",
                "Use monthly focus to improve the build that already has momentum.",
            ],
            how_to_lower=["Forcing upside while debt, stress, or access are failing usually backfires."],
            why_it_matters=["Score is the run verdict. It combines money, access, stability, and wellbeing."],
            common_drivers=["weakest category", "credit", "stress", "career momentum", "housing stability"],
            related_situation_families=["career", "credit", "housing", "transport", "burnout"],
        ),
    ]

    return LearnDrawerVM(
        active_pressure_family=pressure_family,
        credit_line=f"Credit {player.credit_score} ({credit_tier}) | {credit_progress_label}: {credit_progress_detail}",
        stress_line=stress_line,
        pressure_sources=pressure_sources[:5],
        topics=topics,
    )


def build_learn_drawer(source, bundle=None) -> LearnDrawerVM:
    return build_learn_drawer_vm(source, bundle)
