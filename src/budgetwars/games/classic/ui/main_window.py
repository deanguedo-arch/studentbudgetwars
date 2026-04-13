from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from budgetwars.core import GameSession, StartupOptions
from budgetwars.engine.scoring import (
    build_live_score_snapshot,
    credit_progress_summary,
    credit_tier_label,
    dominant_pressure_family,
)
from budgetwars.models import LiveScoreSnapshot

from .theme import (
    BG_CARD, BG_DARK, BG_DARKEST, BG_ELEVATED, BG_HOVER, BG_MID, BORDER,
    TEXT_HEADING, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT_RESOLVE,
    FONT_HEADING, FONT_HEADING_LG, FONT_SUBHEADING, FONT_BODY, FONT_SMALL,
    FONT_MONO, FONT_BUTTON,
    PAD_S, PAD_M, PAD_L, PAD_XL,
    money_str,
)
from .panes import (
    ActionsPanel, FinancePanel, LearnDrawer, LifePanel, LogPanel, OutlookPanel,
    StatusBar, build_menu_bar,
    configure_dark_combobox_style, configure_dark_menu_style,
    show_event_choice_popup, show_milestone_popup, show_endgame_popup,
)
from .choice_previews import (
    _budget_preview,
    _career_branch_preview,
    _career_preview,
    _education_intensity_options,
    _focus_preview,
    _housing_preview,
    _money,
    _transport_preview,
    _wealth_preview,
)
from .diagnostics import (
    _active_status_arc_vms,
    _best_breakdown_category,
    _best_recovery_route,
    _blocked_door_lines,
    _build_crisis_warnings,
    _build_month_outlook_lines,
    _diagnosis_for_family,
    _pending_decision_lines,
    _pressure_map_lines,
    _run_progress_fraction,
    _run_progress_text,
    _score_progress_fraction,
    _score_progress_text,
    _status_arc_diagnosis,
)
from .setup_dialog import (
    _lookup_option,
    build_setup_summary_lines,
    compute_setup_dialog_geometry,
)
from .view_builders import (
    _current_focus_description,
    _current_focus_name,
    _format_persistent_commitments,
    _resolve_context,
)
from .view_models import (
    BuildSnapshotVM,
    BuildSystemVM,
    LearnDrawerVM,
    LearnTopicVM,
    MonthlyForecastVM,
    PressureMetricVM,
    PressureSummaryVM,
    ScoreDeltaVM,
    _SetupGroup,
)


def should_use_compact_layout(width: int, height: int) -> bool:
    # Keep full three-column "one screen" layout on common laptop/desktop sizes.
    # Compact tab mode is now reserved for genuinely constrained windows.
    return width < 1500 or height < 860


def _configure_dark_notebook_style(master: tk.Misc) -> str:
    style = ttk.Style(master)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style_name = "ClassicCompact.TNotebook"
    tab_style = f"{style_name}.Tab"
    style.configure(
        style_name,
        background=BG_DARKEST,
        borderwidth=0,
        tabmargins=(0, 0, 0, 0),
    )
    style.configure(
        tab_style,
        background=BG_CARD,
        foreground=TEXT_SECONDARY,
        padding=(12, 7),
    )
    style.map(
        tab_style,
        background=[("selected", BG_ELEVATED), ("active", BG_MID)],
        foreground=[("selected", TEXT_HEADING), ("active", TEXT_HEADING)],
    )
    return style_name


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
    focus_name = _current_focus_name(controller)
    career_progress = f"Progress: {player.career.promotion_progress}/{career_track.tiers[player.career.tier_index].promotion_target}"
    if player.career.tier_index >= len(career_track.tiers) - 1:
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
    identity_line = (
        f"{career_track.name} | {branch.name if branch is not None else 'Uncommitted lane'} | {wealth.name}"
    )
    commitments = _format_persistent_commitments(player.persistent_tags)
    return BuildSnapshotVM(
        player_name=player.name,
        city_name=city.name,
        identity_line=identity_line,
        persistent_commitments=commitments,
        items=systems,
    )


def build_monthly_forecast_vm(source, bundle=None) -> MonthlyForecastVM:
    controller = _resolve_context(source, bundle)
    state = controller.state
    player = state.player
    focus_name = _current_focus_name(controller)
    focus_description = _current_focus_description(controller)
    warnings = _build_crisis_warnings(state, controller.bundle)
    city = next(item for item in controller.bundle.cities if item.id == player.current_city_id)
    credit_tier = credit_tier_label(player.credit_score)
    credit_progress_label, credit_progress_detail, _ = credit_progress_summary(player.credit_score)
    situation_family = dominant_pressure_family(state)
    blocked_doors = _blocked_door_lines(state, controller.bundle)
    recovery_route = _best_recovery_route(state, controller.bundle)
    active_status_arcs = _active_status_arc_vms(state, controller.bundle)
    main_threat = (
        active_status_arcs[0].summary
        if active_status_arcs
        else (warnings[0] if warnings else (city.pressure_text or "No major threat is pressing right now."))
    )
    best_opportunity = city.opportunity_text
    expected_swing = f"Projected monthly swing {_money(player.monthly_surplus)} before pressure"
    recent_summary = list(state.recent_summary[:3])
    driver_notes = list(state.month_driver_notes[:5])
    if not recent_summary:
        recent_summary = _build_month_outlook_lines(state, controller.bundle)[-2:]
    progress_label, progress_detail = _run_progress_text(state)
    commitments = _format_persistent_commitments(player.persistent_tags)
    return MonthlyForecastVM(
        monthly_focus=focus_description,
        main_threat=main_threat,
        best_opportunity=best_opportunity,
        chosen_focus=focus_name,
        expected_swing=expected_swing,
        situation_family=situation_family,
        credit_status=f"{player.credit_score} {credit_tier} | {credit_progress_label}: {credit_progress_detail}",
        progress_label=progress_label,
        progress_detail=progress_detail,
        progress_fraction=_run_progress_fraction(state),
        persistent_commitments=commitments,
        active_status_arcs=active_status_arcs,
        recovery_route=recovery_route,
        blocked_doors=blocked_doors,
        driver_notes=driver_notes,
        recent_summary=recent_summary,
    )


def build_pressure_summary_vm(source, bundle=None, snapshot: LiveScoreSnapshot | None = None) -> PressureSummaryVM:
    controller = _resolve_context(source, bundle)
    state = controller.state
    player = state.player
    snapshot = snapshot or build_live_score_snapshot(controller.bundle, state)
    credit_tier = credit_tier_label(player.credit_score)
    credit_progress_label, credit_progress_detail, credit_progress_fraction = credit_progress_summary(player.credit_score)
    active_modifiers = [
        f"{modifier.label} ({modifier.remaining_months})"
        for modifier in state.active_modifiers
    ]
    primary_metrics = [
        PressureMetricVM("Cash", _money(player.cash), tone="positive" if player.cash >= 0 else "negative"),
        PressureMetricVM("Savings", _money(player.savings), tone="positive"),
        PressureMetricVM("Debt", _money(player.debt), tone="negative" if player.debt > 0 else "neutral"),
    ]
    secondary_metrics = [
        PressureMetricVM("Income", _money(player.monthly_income), tone="positive"),
        PressureMetricVM("Expenses", _money(player.monthly_expenses), tone="negative"),
        PressureMetricVM("Monthly Swing", _money(player.monthly_surplus), tone="positive" if player.monthly_surplus >= 0 else "negative"),
        PressureMetricVM("Stress", f"{player.stress}/{state.max_stress}", tone="negative" if player.stress >= state.max_stress * 0.75 else "neutral"),
        PressureMetricVM("Energy", f"{player.energy}/{state.max_energy}", tone="negative" if player.energy <= 30 else "neutral"),
        PressureMetricVM("Life", f"{player.life_satisfaction}/{state.max_life_satisfaction}"),
        PressureMetricVM("Family", f"{player.family_support}/{state.max_family_support}"),
        PressureMetricVM("Social", f"{player.social_stability}/{state.max_social_stability}"),
        PressureMetricVM("Housing Stability", f"{player.housing.housing_stability}/100"),
        PressureMetricVM("Transport Reliability", f"{player.transport.reliability_score}/100"),
    ]
    progress_label, progress_detail = _score_progress_text(snapshot.projected_score)
    status_arc_diagnosis = _status_arc_diagnosis(state, controller.bundle)
    run_killer, fastest_fix = status_arc_diagnosis or _diagnosis_for_family(state)
    pressure_family = dominant_pressure_family(state)
    month_driver = (
        state.month_driver_notes[0]
        if state.month_driver_notes
        else _pressure_map_lines(state, controller.bundle)[0]
    )
    blocked_doors = _blocked_door_lines(state, controller.bundle)
    recovery_route = _best_recovery_route(state, controller.bundle)
    commitments = _format_persistent_commitments(player.persistent_tags)
    pending_decisions = _pending_decision_lines(state, controller.bundle)
    active_status_arcs = _active_status_arc_vms(state, controller.bundle)
    biggest_risk = active_status_arcs[0].name if active_status_arcs else snapshot.biggest_risk
    return PressureSummaryVM(
        projected_score=snapshot.projected_score,
        score_tier=snapshot.score_tier,
        biggest_risk=biggest_risk,
        credit_score=player.credit_score,
        credit_tier=credit_tier,
        credit_progress_label=credit_progress_label,
        credit_progress_detail=credit_progress_detail,
        credit_progress_fraction=credit_progress_fraction,
        progress_label=progress_label,
        progress_detail=progress_detail,
        progress_fraction=_score_progress_fraction(snapshot.projected_score),
        run_killer=run_killer,
        fastest_fix=fastest_fix,
        pressure_family=pressure_family,
        month_driver=month_driver,
        active_status_arcs=active_status_arcs,
        recovery_route=recovery_route,
        persistent_commitments=commitments,
        blocked_doors=blocked_doors,
        pending_fallout_count=len(state.pending_events),
        pending_decisions=pending_decisions,
        primary_metrics=primary_metrics,
        secondary_metrics=secondary_metrics,
        active_modifiers=active_modifiers,
        crisis_watch=_build_crisis_warnings(state, controller.bundle),
    )


def build_score_delta_vm(prev_snapshot: LiveScoreSnapshot | None, snapshot: LiveScoreSnapshot) -> ScoreDeltaVM:
    if prev_snapshot is None:
        delta = 0.0
        prev_score = None
        prev_tier = None
    else:
        prev_score = prev_snapshot.projected_score
        prev_tier = prev_snapshot.score_tier
        delta = round(snapshot.projected_score - prev_snapshot.projected_score, 2)
    return ScoreDeltaVM(
        previous_score=prev_score,
        current_score=snapshot.projected_score,
        delta=delta,
        previous_tier=prev_tier,
        tier=snapshot.score_tier,
        strongest_category=_best_breakdown_category(snapshot.breakdown, reverse=True),
        weakest_category=_best_breakdown_category(snapshot.breakdown, reverse=False),
        diagnosis=snapshot.biggest_risk,
    )


def build_build_snapshot(source, bundle=None) -> BuildSnapshotVM:
    return build_build_snapshot_vm(source, bundle)


def build_monthly_forecast(source, bundle=None) -> MonthlyForecastVM:
    return build_monthly_forecast_vm(source, bundle)


def build_pressure_summary(source, bundle=None, snapshot: LiveScoreSnapshot | None = None) -> PressureSummaryVM:
    return build_pressure_summary_vm(source, bundle, snapshot=snapshot)


def build_score_delta_summary(
    prev_snapshot: LiveScoreSnapshot | None,
    snapshot: LiveScoreSnapshot,
) -> ScoreDeltaVM:
    return build_score_delta_vm(prev_snapshot, snapshot)


def build_learn_drawer(source, bundle=None) -> LearnDrawerVM:
    return build_learn_drawer_vm(source, bundle)


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


class SelectionDialog(simpledialog.Dialog):
    """Dark-themed selection dialog for choosing game options."""

    def __init__(self, parent: tk.Misc, title: str, prompt: str, options: list[tuple[str, str, str]]):
        self.prompt = prompt
        self.options = options
        self.result: str | None = None
        self._desc_var = tk.StringVar(value="")
        super().__init__(parent, title)

    def body(self, master: tk.Misc):
        master.configure(bg=BG_DARKEST)
        self.configure(bg=BG_DARKEST)

        tk.Label(master, text=self.prompt, justify="left", wraplength=540,
                 font=FONT_SUBHEADING, bg=BG_DARKEST, fg=TEXT_HEADING).pack(
            anchor="w", padx=PAD_M, pady=(PAD_M, PAD_S)
        )
        self.listbox = tk.Listbox(
            master, width=56, height=min(9, max(4, len(self.options))),
            font=FONT_BODY,
            bg=BG_ELEVATED, fg=TEXT_HEADING,
            selectbackground=ACCENT_RESOLVE, selectforeground=TEXT_HEADING,
            relief="flat", bd=0,
            highlightbackground=BORDER, highlightthickness=1,
            activestyle="none",
            exportselection=False,
        )
        self.listbox.pack(fill="both", expand=True, padx=PAD_M, pady=PAD_S)
        for label, _, _ in self.options:
            self.listbox.insert("end", label)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        tk.Label(
            master,
            textvariable=self._desc_var,
            justify="left", anchor="w", wraplength=540,
            bg=BG_CARD, fg=TEXT_SECONDARY,
            relief="flat", bd=0,
            padx=PAD_M, pady=PAD_S,
            font=FONT_SMALL,
        ).pack(fill="x", padx=PAD_M, pady=(0, PAD_M))

        if self.options:
            self.listbox.selection_set(0)
            self._desc_var.set(self.options[0][2])
        return self.listbox

    def _on_select(self, _event=None) -> None:
        if self.listbox.curselection():
            self._desc_var.set(self.options[self.listbox.curselection()[0]][2])

    def apply(self):
        if self.listbox.curselection():
            self.result = self.options[self.listbox.curselection()[0]][1]

    def buttonbox(self):
        box = tk.Frame(self, bg=BG_DARKEST)
        ok_btn = tk.Button(box, text="OK", width=10, command=self.ok, default="active",
                           bg=BG_ELEVATED, fg=TEXT_PRIMARY, activebackground=BG_HOVER,
                           font=FONT_BUTTON, relief="flat", cursor="hand2",
                           highlightbackground=BORDER, highlightthickness=1)
        ok_btn.pack(side="left", padx=5, pady=PAD_M)
        cancel_btn = tk.Button(box, text="Cancel", width=10, command=self.cancel,
                               bg=BG_DARK, fg=TEXT_SECONDARY, activebackground=BG_ELEVATED,
                               font=FONT_BUTTON, relief="flat", cursor="hand2",
                               highlightbackground=BORDER, highlightthickness=1)
        cancel_btn.pack(side="left", padx=5, pady=PAD_M)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()


class ClassicSetupDialog(simpledialog.Dialog):
    def __init__(
        self,
        parent: tk.Misc,
        bundle,
        *,
        initial_name: str = "Player",
        initial_preset_id: str | None = None,
        initial_city_id: str | None = None,
        initial_academic_level_id: str | None = None,
        initial_family_support_level_id: str | None = None,
        initial_savings_band_id: str | None = None,
        initial_opening_path_id: str | None = None,
        initial_difficulty_id: str | None = None,
    ):
        self.bundle = bundle
        self.result: dict[str, str] | None = None
        self.player_name_var = tk.StringVar(value=initial_name or "Player")
        self.summary_var = tk.StringVar(value="")
        self._group_selection_vars: dict[str, tk.StringVar] = {}
        self._group_desc_vars: dict[str, tk.StringVar] = {}
        self._group_buttons: dict[str, tk.Button] = {}
        self._value_maps: dict[str, dict[str, tuple[str, str, str]]] = {}
        self._groups = [
            _SetupGroup(
                "preset_id", "Preset",
                "Choose the background you are starting from:",
                [(item.name, item.id, item.description) for item in bundle.presets],
                initial_preset_id,
            ),
            _SetupGroup(
                "city_id", "City",
                "Choose the city you are trying to make work:",
                [(item.name, item.id, item.opportunity_text) for item in bundle.cities],
                initial_city_id,
            ),
            _SetupGroup(
                "academic_level_id", "Academics",
                "How strong is your academic footing?",
                [(item.name, item.id, item.description) for item in bundle.config.academic_levels],
                initial_academic_level_id,
            ),
            _SetupGroup(
                "family_support_level_id", "Family Support",
                "How much backup do you realistically have?",
                [(item.name, item.id, item.description) for item in bundle.config.family_support_levels],
                initial_family_support_level_id,
            ),
            _SetupGroup(
                "savings_band_id", "Starting Cushion",
                "How much cushion are you really starting with?",
                [(item.name, item.id, item.description) for item in bundle.config.savings_bands],
                initial_savings_band_id,
            ),
            _SetupGroup(
                "opening_path_id", "Opening Path",
                "Pick the lane you are stepping into first:",
                [(item.name, item.id, item.description) for item in bundle.config.opening_paths],
                initial_opening_path_id,
            ),
            _SetupGroup(
                "difficulty_id", "Difficulty",
                "Pick how hard the decade should hit back:",
                [(item.name, item.id, item.description) for item in bundle.difficulties],
                initial_difficulty_id,
            ),
        ]
        self._groups_by_key = {group.key: group for group in self._groups}
        super().__init__(parent, "Start New Run")

    def body(self, master: tk.Misc):
        master.configure(bg=BG_DARKEST)
        self.configure(bg=BG_DARKEST)
        self._combobox_style = configure_dark_combobox_style(self)
        self.transient(self.master)
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=5)
        master.columnconfigure(1, weight=4)

        left = tk.Frame(master, bg=BG_DARKEST)
        left.grid(row=0, column=0, sticky="nsew", padx=(PAD_M, PAD_M), pady=PAD_M)
        left.columnconfigure(0, weight=1)

        name_frame = tk.LabelFrame(left, text="Player Name", padx=PAD_M, pady=PAD_M,
                                   bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SUBHEADING,
                                   bd=1, relief="solid", highlightbackground=BORDER,
                                   highlightthickness=1)
        name_frame.grid(row=0, column=0, sticky="ew", pady=(0, PAD_M))
        self.name_entry = tk.Entry(name_frame, textvariable=self.player_name_var,
                                   font=FONT_BODY, bg=BG_ELEVATED, fg=TEXT_PRIMARY,
                                   insertbackground=TEXT_PRIMARY, relief="flat",
                                   highlightbackground=BORDER, highlightthickness=1)
        self.name_entry.pack(fill="x")

        # Scrollable options
        options_outer = tk.LabelFrame(left, text="Start Setup", padx=PAD_M, pady=PAD_M,
                                      bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SUBHEADING,
                                      bd=1, relief="solid", highlightbackground=BORDER,
                                      highlightthickness=1)
        options_outer.grid(row=1, column=0, sticky="nsew")
        options_outer.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        canvas = tk.Canvas(options_outer, bg=BG_CARD, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(options_outer, orient="vertical", command=canvas.yview)
        options_frame = tk.Frame(canvas, bg=BG_CARD)
        options_frame.columnconfigure(0, weight=1)

        options_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        options_window = canvas.create_window((0, 0), window=options_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(options_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for row, group in enumerate(self._groups):
            option_map = {label: option for option in group.options for label in [option[0]]}
            self._value_maps[group.key] = option_map
            option_labels = list(option_map)
            default_option = _lookup_option(group.options, group.initial_id)
            var = tk.StringVar(value=default_option[0])
            desc_var = tk.StringVar(value=default_option[2])
            self._group_selection_vars[group.key] = var
            self._group_desc_vars[group.key] = desc_var

            frame = tk.LabelFrame(options_frame, text=group.title, padx=PAD_M, pady=PAD_S,
                                  bg=BG_ELEVATED, fg=TEXT_HEADING, font=FONT_SMALL,
                                  bd=0, relief="flat")
            frame.grid(row=row, column=0, sticky="ew", pady=3)
            frame.columnconfigure(0, weight=1)

            select_btn = tk.Button(
                frame,
                textvariable=var,
                command=lambda key=group.key: self.select_setup_group(key),
                bg=BG_MID,
                fg=TEXT_PRIMARY,
                activebackground=BG_HOVER,
                activeforeground=TEXT_HEADING,
                font=FONT_BODY,
                relief="flat",
                cursor="hand2",
                highlightbackground=BORDER,
                highlightthickness=1,
                anchor="w",
                padx=PAD_M,
                pady=PAD_S,
            )
            select_btn.grid(row=0, column=0, sticky="ew")
            self._group_buttons[group.key] = select_btn

            tk.Label(
                frame, text=group.prompt, justify="left", wraplength=400,
                fg=TEXT_SECONDARY, bg=BG_ELEVATED, font=("Segoe UI", 9, "bold"),
            ).grid(row=1, column=0, sticky="w", pady=(PAD_S, 0))
            tk.Label(
                frame, textvariable=desc_var, justify="left", wraplength=400,
                fg=TEXT_MUTED, bg=BG_ELEVATED, font=FONT_SMALL,
            ).grid(row=2, column=0, sticky="w", pady=(2, 0))

        right = tk.LabelFrame(master, text="Opening Identity", padx=PAD_L, pady=PAD_L,
                              bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SUBHEADING,
                              bd=1, relief="solid", highlightbackground=BORDER,
                              highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew", padx=(0, PAD_M), pady=PAD_M)
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self.summary_text = tk.Text(
            right, width=1, height=1, wrap="word",
            bg=BG_ELEVATED, fg=TEXT_PRIMARY,
            relief="flat", bd=0,
            font=FONT_BODY, spacing1=2, spacing3=4,
            insertbackground=BG_ELEVATED,
        )
        self.summary_text.grid(row=0, column=0, sticky="nsew")
        self.summary_text.configure(state="disabled")

        self.update_idletasks()
        parent = self.master
        parent.update_idletasks()
        x, y, width, height = compute_setup_dialog_geometry(
            parent_x=parent.winfo_rootx(),
            parent_y=parent.winfo_rooty(),
            parent_width=max(1, parent.winfo_width()),
            parent_height=max(1, parent.winfo_height()),
            screen_width=self.winfo_screenwidth(),
            screen_height=self.winfo_screenheight(),
        )
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(min(860, width), min(600, height))

        self._refresh_summary()
        return self.name_entry

    def _current_option(self, key: str) -> tuple[str, str, str]:
        selected_label = self._group_selection_vars[key].get()
        return self._value_maps[key][selected_label]

    def _selected_ids(self) -> dict[str, str]:
        return {key: self._current_option(key)[1] for key in self._group_selection_vars}

    def select_setup_group(self, key: str) -> None:
        group = self._groups_by_key[key]
        choice = SelectionDialog(self, group.title, group.prompt, group.options).result
        if choice is None:
            return
        selected = next(option for option in group.options if option[1] == choice)
        self._group_selection_vars[key].set(selected[0])
        self._group_desc_vars[key].set(selected[2])
        self._group_buttons[key].configure(text=selected[0])
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        selections = self._selected_ids()
        summary_lines = build_setup_summary_lines(self.bundle, selections, self.player_name_var.get().strip())
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", "\n".join(summary_lines))
        self.summary_text.configure(state="disabled")

    def validate(self) -> bool:
        if not self.player_name_var.get().strip():
            messagebox.showerror("Player Name", "Please enter a player name.")
            return False
        return True

    def apply(self) -> None:
        self.result = {
            "player_name": self.player_name_var.get().strip() or "Player",
            **self._selected_ids(),
        }

    def buttonbox(self):
        box = tk.Frame(self, bg=BG_DARKEST)
        start = tk.Button(box, text="Start Run", width=14, command=self.ok, default="active",
                          bg="#4a4520", fg=ACCENT_RESOLVE, activebackground="#5a5528",
                          font=("Segoe UI", 12, "bold"), relief="flat", cursor="hand2",
                          highlightbackground=ACCENT_RESOLVE, highlightthickness=2)
        start.pack(side="left", padx=5, pady=PAD_M)
        cancel = tk.Button(box, text="Cancel", width=10, command=self.cancel,
                           bg=BG_DARK, fg=TEXT_SECONDARY, activebackground=BG_ELEVATED,
                           font=FONT_BUTTON, relief="flat", cursor="hand2",
                           highlightbackground=BORDER, highlightthickness=1)
        cancel.pack(side="left", padx=5, pady=PAD_M)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()


def prompt_new_game_setup(
    parent: tk.Misc,
    bundle,
    *,
    initial_name: str = "Player",
    initial_preset_id: str | None = None,
    initial_city_id: str | None = None,
    initial_academic_level_id: str | None = None,
    initial_family_support_level_id: str | None = None,
    initial_savings_band_id: str | None = None,
    initial_opening_path_id: str | None = None,
    initial_difficulty_id: str | None = None,
) -> dict[str, str] | None:
    dialog = ClassicSetupDialog(
        parent,
        bundle,
        initial_name=initial_name,
        initial_preset_id=initial_preset_id,
        initial_city_id=initial_city_id,
        initial_academic_level_id=initial_academic_level_id,
        initial_family_support_level_id=initial_family_support_level_id,
        initial_savings_band_id=initial_savings_band_id,
        initial_opening_path_id=initial_opening_path_id,
        initial_difficulty_id=initial_difficulty_id,
    )
    return dialog.result


class MainWindow(tk.Frame):
    def __init__(self, master: tk.Tk, session: GameSession):
        super().__init__(master, bg=BG_DARKEST)
        self.master = master
        self.session = session
        self._result_announced = False
        self._shown_milestone_count = 0
        self._large_text = False
        self._compact_layout_auto = should_use_compact_layout(
            self.master.winfo_screenwidth(),
            self.master.winfo_screenheight(),
        )
        self._compact_layout_override: bool | None = None
        self._layout_compact_active: bool | None = None
        self._previous_snapshot = None
        self._previous_credit_score = None
        self._latest_snapshot = None
        self.score_strip = None
        self._learn_visible = False
        self._learn_drawer = None
        self.pack(fill="both", expand=True)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_layout()
        self._apply_text_scale()
        self.refresh()

    @property
    def controller(self):
        return self.session.require_controller()

    def _desired_compact_layout(self, *, use_current_window: bool = True) -> bool:
        if self._compact_layout_override is not None:
            return self._compact_layout_override
        if use_current_window:
            current = should_use_compact_layout(
                max(1, self.master.winfo_width()),
                max(1, self.master.winfo_height()),
            )
        else:
            current = self._compact_layout_auto
        return self._compact_layout_auto or current

    def _clear_main_content(self) -> None:
        for child in self._content_frame.winfo_children():
            child.destroy()

    def _build_standard_main_content(self) -> None:
        content = self._content_frame
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=5)
        content.grid_columnconfigure(2, weight=3)

        self.life_panel = LifePanel(content, "Build", on_action=self._on_build_card_action)
        self.life_panel.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_S))

        center = tk.Frame(content, bg=BG_DARKEST)
        center.grid(row=0, column=1, sticky="nsew", padx=PAD_S)
        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(0, weight=3)
        center.grid_rowconfigure(1, weight=2)
        self.outlook_panel = OutlookPanel(center, "This Month", resolve_callback=self.resolve_month)
        self.outlook_panel.grid(row=0, column=0, sticky="nsew", pady=(0, PAD_S))
        self.log_panel = LogPanel(center, "Run Feedback")
        self.log_panel.grid(row=1, column=0, sticky="nsew")

        self.finance_panel = FinancePanel(content, "Score & Pressure")
        self.finance_panel.grid(row=0, column=2, sticky="nsew", padx=(PAD_S, 0))

    def _build_compact_main_content(self) -> None:
        content = self._content_frame
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        notebook = ttk.Notebook(content, style=_configure_dark_notebook_style(self.master))
        notebook.grid(row=0, column=0, sticky="nsew")
        self._compact_notebook = notebook

        build_tab = tk.Frame(notebook, bg=BG_DARKEST)
        month_tab = tk.Frame(notebook, bg=BG_DARKEST)
        pressure_tab = tk.Frame(notebook, bg=BG_DARKEST)
        notebook.add(build_tab, text="Build")
        notebook.add(month_tab, text="This Month")
        notebook.add(pressure_tab, text="Score & Pressure")
        notebook.select(month_tab)

        self.life_panel = LifePanel(build_tab, "Build", on_action=self._on_build_card_action)
        self.life_panel.pack(fill="both", expand=True)

        month_tab.grid_rowconfigure(0, weight=2)
        month_tab.grid_rowconfigure(1, weight=1)
        month_tab.grid_columnconfigure(0, weight=1)
        self.outlook_panel = OutlookPanel(month_tab, "This Month", resolve_callback=self.resolve_month)
        self.outlook_panel.grid(row=0, column=0, sticky="nsew", pady=(0, PAD_S))
        self.log_panel = LogPanel(month_tab, "Run Feedback")
        self.log_panel.grid(row=1, column=0, sticky="nsew")

        self.finance_panel = FinancePanel(pressure_tab, "Score & Pressure")
        self.finance_panel.pack(fill="both", expand=True)

    def _build_layout(self) -> None:
        # ── Status bar (top) ──
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=0, column=0, sticky="ew", padx=PAD_M, pady=(PAD_M, PAD_S))

        # ── Main content area ──
        content = tk.Frame(self, bg=BG_DARKEST)
        self._content_frame = content
        content.grid(row=1, column=0, sticky="nsew", padx=PAD_M, pady=(0, PAD_S))
        self._compact_notebook = None
        self._layout_compact_active = None
        self._build_main_content(self._desired_compact_layout(use_current_window=False))

        # ── Actions bar (bottom) ── (hidden; replaced by clickable side cards)
        self.actions_panel = ActionsPanel(self)
        self.actions_panel.grid(row=3, column=0, sticky="ew", padx=PAD_M, pady=(0, PAD_M))
        self.actions_panel.grid_remove()

        self.master.config(
            menu=build_menu_bar(
                self.master,
                {
                    "new_game": self.restart_new_game,
                    "save": self.save_game,
                    "exit": self.master.destroy,
                    "career": self.change_career,
                    "education": self.change_education,
                    "housing": self.change_housing,
                    "transport": self.change_transport,
                    "budget": self.change_budget,
                    "wealth": self.change_wealth,
                    "focus": self.change_focus,
                    "resolve": self.resolve_month,
                    "text_size": self.toggle_large_text,
                    "compact_layout": self.toggle_compact_layout,
                    "score": self.show_score_projection,
                    "learn": self.show_learn,
                    "help": self.show_help,
                },
            )
        )

    def _build_main_content(self, compact: bool) -> None:
        self._clear_main_content()
        self._layout_compact_active = compact
        if compact:
            self._build_compact_main_content()
        else:
            self._build_standard_main_content()

    def _choose(self, title: str, prompt: str, options: list[tuple[str, str, str]]) -> str | None:
        if not options:
            messagebox.showinfo(title, "No valid options right now.")
            return None
        dialog = SelectionDialog(self.master, title, prompt, options)
        return dialog.result

    def _build_action_groups(self, *, compact: bool = False) -> list[tuple[str, list[tuple[str, object]]]]:
        monthly_actions: list[tuple[str, object]] = [("Focus", self.change_focus)]
        if self.controller.available_win_states():
            monthly_actions.append(("Claim Victory", self.claim_victory))
        monthly_actions.append(("Resolve Month", self.resolve_month))
        return [
            ("Build", [
                ("Career", self.change_career),
                ("Education", self.change_education),
                ("Housing", self.change_housing),
                ("Transport", self.change_transport),
            ]),
            ("Policy", [
                ("Budget", self.change_budget),
                ("Wealth", self.change_wealth),
            ]),
            ("This Month", monthly_actions),
        ]

    def _auto_save(self) -> None:
        self.session.autosave()

    def _after_action(self) -> None:
        self._auto_save()
        self.refresh()
        if self._check_pending_event_choice():
            self._auto_save()
            self.refresh()
        if self._check_pending_promotion_branch_choice():
            self._auto_save()
            self.refresh()
        self._check_milestones()
        self._check_end_state()

    def _run_action(self, callback) -> None:
        try:
            callback()
            self._after_action()
        except ValueError as exc:
            messagebox.showerror("Action failed", str(exc))
            self.refresh()

    def _life_lines(self) -> list[str]:
        vm = build_build_snapshot_vm(self.controller)
        lines = [vm.headline, f"Opening path: {self.controller.state.player.opening_path_id.replace('_', ' ').title()}", ""]
        for system in vm.systems:
            lines.append(f"{system.system}: {system.primary}")
            if system.detail:
                lines.append(system.detail)
        return lines

    def _outlook_lines(self) -> list[str]:
        vm = build_monthly_forecast_vm(self.controller)
        outlook = [
            f"Monthly focus: {vm.chosen_focus}",
            vm.monthly_focus,
            f"Situation family: {vm.situation_family}",
            f"Credit: {vm.credit_status}",
            "",
            f"Main threat: {vm.main_threat}",
            f"Best opportunity: {vm.best_opportunity}",
            f"Expected swing: {vm.expected_swing}",
        ]
        if vm.recovery_route:
            outlook += ["", vm.recovery_route]
        if vm.active_status_arcs:
            outlook += ["", "Active arcs:"]
            for arc in vm.active_status_arcs[:2]:
                outlook.append(f"{arc.name} | S{arc.severity} | {arc.months_remaining}mo")
        if vm.blocked_doors:
            outlook += ["", "Blocked doors:"] + vm.blocked_doors[:2]
        if vm.driver_notes:
            outlook += ["", "Why this month matters:"] + vm.driver_notes
        if vm.recent_summary:
            outlook += ["", "Last month:"] + vm.recent_summary
        return outlook[:16]

    def _finance_lines(self) -> list[str]:
        vm = build_pressure_summary_vm(self.controller, snapshot=self._latest_snapshot)
        delta_vm = build_score_delta_vm(self._previous_snapshot, self._latest_snapshot or self.controller.live_score_snapshot())
        lines = [
            f"Projected Score: {vm.projected_score:.2f}",
            f"Tier: {vm.tier}",
            f"Score change: {delta_vm.delta:+.2f}",
            f"Credit: {vm.credit_score} {vm.credit_tier}",
            f"{vm.credit_progress_label}: {vm.credit_progress_detail}",
            f"Strongest category: {delta_vm.strongest_category}",
            f"Weakest category: {delta_vm.weakest_category}",
            f"Biggest Risk: {vm.biggest_risk}",
            "",
        ]
        lines.extend(f"{metric.label}: {metric.primary}" for metric in vm.primary_metrics)
        lines.append("")
        lines.extend(f"{metric.label}: {metric.primary}" for metric in vm.secondary_metrics[:5])
        lines.append("")
        if vm.recovery_route:
            lines.append(vm.recovery_route)
            lines.append("")
        if vm.active_status_arcs:
            lines.append("Active Arcs:")
            for arc in vm.active_status_arcs[:2]:
                lines.append(f"{arc.name} | S{arc.severity} | {arc.months_remaining}mo")
            lines.append("")
        if vm.blocked_doors:
            lines.append("Blocked Doors:")
            lines.extend(vm.blocked_doors[:2])
            lines.append("")
        lines.append("Active Modifiers:")
        lines.append(", ".join(vm.active_modifiers) if vm.active_modifiers else "None")
        lines.append("")
        lines.append("Crisis Watch:")
        lines.extend(vm.crisis_watch or ["Stable enough for now."])
        return lines

    def refresh(self) -> None:
        state = self.controller.state
        window_width = max(1, self.master.winfo_width())
        window_height = max(1, self.master.winfo_height())
        if self._large_text and (window_height < 1080 or window_width < 1900):
            # Prevent layout blowups on common laptop/desktop sizes.
            self._large_text = False
            self._apply_text_scale()
        compact = self._desired_compact_layout()
        if compact != self._layout_compact_active:
            self._build_main_content(compact)
            self._apply_text_scale()
        dense_noncompact = (not compact) and (self._large_text or window_height < 980)
        panel_compact = compact or dense_noncompact
        previous_credit = self._previous_credit_score
        self._previous_snapshot = self._latest_snapshot
        self._latest_snapshot = self.controller.live_score_snapshot()
        self._previous_credit_score = state.player.credit_score
        delta_vm = build_score_delta_vm(self._previous_snapshot, self._latest_snapshot)
        credit_delta = None if previous_credit is None else state.player.credit_score - previous_credit
        self.status_bar.render(
            state,
            self.controller.bundle,
            self._latest_snapshot,
            delta_vm,
            credit_score=state.player.credit_score,
            credit_delta=credit_delta,
        )
        self.life_panel.render_snapshot(build_build_snapshot_vm(self.controller), compact=panel_compact)
        self.outlook_panel.render_forecast(
            build_monthly_forecast_vm(self.controller),
            compact=panel_compact,
            show_resolve_button=True,
        )
        self.finance_panel.render_summary(
            build_pressure_summary_vm(self.controller, snapshot=self._latest_snapshot),
            delta_vm,
            credit_delta=credit_delta,
            compact=panel_compact,
        )
        if self._learn_drawer is not None and self._learn_drawer.winfo_exists():
            self._learn_drawer.render(build_learn_drawer_vm(self.controller))
        self.log_panel.render(self._run_feedback_lines(), limit=6 if panel_compact else 10)
        size_tag = "Large Text" if self._large_text else "Normal Text"
        self.master.title(f"{state.game_title} - {state.player.name} ({size_tag})")

    def _run_feedback_lines(self) -> list[str]:
        state = self.controller.state
        crisis = self.controller.build_crisis_warnings()
        next_best_move = _current_focus_name(self.controller)
        family = dominant_pressure_family(state)
        recovery_route = _best_recovery_route(state, self.controller.bundle)
        month_driver = (
            state.month_driver_notes[0]
            if state.month_driver_notes
            else _pressure_map_lines(state, self.controller.bundle)[0]
        )
        pending_decisions = _pending_decision_lines(state, self.controller.bundle)
        lines = [
            f"Big Win: {state.recent_summary[0]}" if state.recent_summary else "Big Win: Holding steady.",
            f"Big Hit: {state.recent_summary[1]}" if len(state.recent_summary) > 1 else "Big Hit: No major hit this month.",
            f"Score Change: {self._latest_snapshot.projected_score:.1f}" if self._latest_snapshot else "Score Change: Pending.",
            f"Situation Family: {family}",
            f"Month Driver: {month_driver}",
            f"New Threat: {crisis[0]}" if crisis else "New Threat: None right now.",
            f"Next Best Move: {next_best_move}",
        ]
        if state.pending_events:
            lines.append(f"Pending Fallout: {len(state.pending_events)} unresolved consequence(s).")
        lines.extend(pending_decisions)
        if recovery_route:
            lines.append(f"Recovery Route: {recovery_route.replace('Best recovery route: ', '')}")
        return lines + state.log_messages

    def _apply_text_scale(self) -> None:
        self.status_bar.set_large_text(self._large_text)
        self.life_panel.set_large_text(self._large_text)
        self.outlook_panel.set_large_text(self._large_text)
        self.finance_panel.set_large_text(self._large_text)
        self.log_panel.set_large_text(self._large_text)
        if self.actions_panel is not None:
            self.actions_panel.set_large_text(self._large_text)
        if self.score_strip is not None:
            self.score_strip.set_large_text(self._large_text)

    def _on_build_card_action(self, action_key: str) -> None:
        action_map = {
            "career": self.change_career,
            "education": self.change_education,
            "housing": self.change_housing,
            "transport": self.change_transport,
            "wealth": self.change_wealth,
            "focus": self.change_focus,
        }
        callback = action_map.get(action_key)
        if callback is None:
            return
        self._run_action(callback)

    def toggle_large_text(self) -> None:
        self._large_text = not self._large_text
        self._apply_text_scale()
        self.refresh()

    def toggle_compact_layout(self) -> None:
        current = self._desired_compact_layout()
        self._compact_layout_override = not current
        self.refresh()

    def _check_milestones(self) -> None:
        if len(self.controller.state.annual_milestones) <= self._shown_milestone_count:
            return
        latest = self.controller.state.annual_milestones[-1]
        show_milestone_popup(self.master, latest.summary_lines)
        self._shown_milestone_count = len(self.controller.state.annual_milestones)

    def _check_end_state(self) -> None:
        if self._result_announced or not self.controller.is_finished():
            return
        summary = self.controller.final_score_summary()
        show_endgame_popup(
            self.master,
            ending_label=summary.ending_label,
            outcome=summary.outcome,
            final_score=summary.final_score,
            breakdown=summary.breakdown,
        )
        self._result_announced = True

    def _check_pending_event_choice(self) -> bool:
        pending_event = self.controller.state.pending_user_choice_event
        event_id = self.controller.state.pending_user_choice_event_id
        if not event_id:
            return False
        event = pending_event or next((item for item in self.controller.bundle.events if item.id == event_id), None)
        if event is None or not event.choices:
            return False
        choice = show_event_choice_popup(
            self.master,
            title=event.name,
            prompt=event.description,
            choices=[(item.label, item.id, item.description, item.stat_effects) for item in event.choices],
        )
        if choice is None:
            return False
        self.controller.resolve_event_choice(choice)
        return True

    def _check_pending_promotion_branch_choice(self) -> bool:
        options = []
        for branch, allowed, reason in self.controller.pending_promotion_branch_choices():
            if not allowed:
                continue
            options.append((branch.name, branch.id, _career_branch_preview(branch)))
        if not options:
            return False
        chosen = self._choose(
            "Promotion Branch",
            "Promotion is waiting on a branch decision. Choose your path:",
            options,
        )
        if chosen is None:
            return False
        self.controller.choose_career_branch(chosen)
        return True

    def restart_new_game(self) -> None:
        bundle = self.session.refresh_bundle()
        setup = prompt_new_game_setup(self.master, bundle)
        if not setup:
            return
        self.session.start_new_game(
            StartupOptions(
                mode="classic",
                player_name=setup["player_name"],
                preset_id=setup["preset_id"],
                difficulty_id=setup["difficulty_id"],
                city_id=setup["city_id"],
                opening_path_id=setup["opening_path_id"],
                academic_level_id=setup["academic_level_id"],
                family_support_level_id=setup["family_support_level_id"],
                savings_band_id=setup["savings_band_id"],
            )
        )
        self._result_announced = False
        self._shown_milestone_count = 0
        self._previous_snapshot = None
        self._latest_snapshot = None
        self._previous_credit_score = None
        self._after_action()

    def change_career(self) -> None:
        branch_options = []
        for branch, allowed, reason in self.controller.available_career_branches():
            if allowed:
                branch_options.append((f"Branch: {branch.name}", branch.id, _career_branch_preview(branch)))
        if branch_options:
            chosen_branch = self._choose("Career Branch", "Choose a branch for your current career lane:", branch_options)
            if chosen_branch:
                self._run_action(lambda: self.controller.choose_career_branch(chosen_branch))
                return
        options: list[tuple[str, str, str]] = []
        for name, track_id, allowed, reason in self.controller.career_entry_statuses():
            if not allowed:
                continue
            track = next(track for track in self.controller.bundle.careers if track.id == track_id)
            description = _career_preview(track)
            options.append((name, track_id, description))
        chosen = self._choose("Career", "Choose your career lane:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_career(chosen))

    def change_education(self) -> None:
        options = [(program.name, program.id, program.description) for program in self.controller.available_education_programs()]
        chosen = self._choose("Education", "Choose your education plan. Picking the current plan toggles pause/resume.", options)
        if chosen:
            if chosen != "none":
                program = next(item for item in self.controller.bundle.education_programs if item.id == chosen)
                intensity = self._choose(
                    "Education Intensity",
                    "How hard are you pushing this month?",
                    _education_intensity_options(program),
                )
                if intensity:
                    self._run_action(lambda: self.controller.change_education(chosen, intensity))
            else:
                self._run_action(lambda: self.controller.change_education(chosen))

    def _education_intensity_options(self):
        program = next(
            (item for item in self.controller.bundle.education_programs if item.id == self.controller.state.player.education.program_id),
            None,
        )
        return _education_intensity_options(program)

    def change_housing(self) -> None:
        options = [
            (f"{option.name} | move {_money(option.move_in_cost)}", option.id, _housing_preview(option))
            for option in self.controller.available_housing()
        ]
        chosen = self._choose("Housing", "Choose your housing setup:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_housing(chosen))

    def change_transport(self) -> None:
        discount = self.controller.current_transport_switch_discount()
        options = []
        for option in self.controller.available_transport():
            upfront = max(0, option.upfront_cost - discount)
            monthly = option.monthly_payment + option.insurance_cost + option.fuel_maintenance_cost
            options.append((f"{option.name} | upfront {_money(upfront)} | monthly {_money(monthly)}", option.id, _transport_preview(option, upfront, monthly)))
        chosen = self._choose("Transport", "Choose your transport setup:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_transport(chosen))

    def change_budget(self) -> None:
        options = [(stance.name, stance.id, _budget_preview(stance)) for stance in self.controller.available_budget_stances()]
        chosen = self._choose("Budget", "Choose your monthly budget stance:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_budget_stance(chosen))

    def change_wealth(self) -> None:
        options = [(strategy.name, strategy.id, _wealth_preview(strategy)) for strategy in self.controller.available_wealth_strategies()]
        chosen = self._choose("Wealth Strategy", "Choose how you want extra money to behave each month:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_wealth_strategy(chosen))

    def change_focus(self) -> None:
        options = [(focus.name, focus.id, _focus_preview(focus)) for focus in self.controller.available_focus_actions()]
        chosen = self._choose("Focus", "Choose this month's focus:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_focus_action(chosen))

    def claim_victory(self) -> None:
        options = [
            (
                f"{state.name} | x{state.score_multiplier:.2f}",
                state.id,
                state.description,
            )
            for state in self.controller.available_win_states()
        ]
        chosen = self._choose("Victory", "Choose the victory lane you are ready to claim:", options)
        if chosen:
            self._run_action(lambda: self.controller.declare_victory(chosen))

    def resolve_month(self) -> None:
        self._run_action(self.controller.resolve_month)

    def save_game(self) -> None:
        default_name = self.controller.bundle.config.autosave_name
        save_name = simpledialog.askstring("Save Game", "Save file name:", initialvalue=default_name, parent=self.master)
        if not save_name:
            return
        self.session.save_named(save_name)
        messagebox.showinfo("Saved", f"Saved to {save_name}")

    def show_score_projection(self) -> None:
        summary = self.controller.final_score_summary()
        show_endgame_popup(
            self.master,
            ending_label=summary.ending_label,
            outcome=summary.outcome,
            final_score=summary.final_score,
            breakdown=summary.breakdown,
        )

    def show_help(self) -> None:
        messagebox.showinfo(
            "How To Play",
            "Each turn is one month.\n\n"
            "Your persistent setup is your career lane, education plan, housing, transport, budget stance, and wealth plan.\n"
            "You also control a separate monthly focus that shapes the next resolve.\n"
            "Choose a setup, pick a focus, then resolve the month and react to the pressure that follows.\n\n"
            "Open Info > Learn if you need a quick explanation of what raises or lowers your stats.\n\n"
            "The goal is to chase the strongest score you can build before age 28.",
        )

    def show_learn(self) -> None:
        self._learn_visible = not self._learn_visible
        if self._learn_visible:
            if self._learn_drawer is None or not self._learn_drawer.winfo_exists():
                self._learn_drawer = LearnDrawer(self.master, on_close=self._on_learn_close)
            self._learn_drawer.render(build_learn_drawer_vm(self.controller))
            self._learn_drawer.focus_force()
        else:
            self._on_learn_close()

    def _on_learn_close(self) -> None:
        self._learn_visible = False
        if self._learn_drawer is None:
            return
        if self._learn_drawer.winfo_exists():
            self._learn_drawer.destroy()
        self._learn_drawer = None
