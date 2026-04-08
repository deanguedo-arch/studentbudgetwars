from __future__ import annotations

from dataclasses import dataclass, field

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from budgetwars.core import GameSession, StartupOptions
from budgetwars.engine.scoring import build_live_score_snapshot
from budgetwars.models import LiveScoreSnapshot

from .theme import (
    BG_CARD, BG_DARK, BG_DARKEST, BG_ELEVATED, BG_HOVER, BORDER,
    TEXT_HEADING, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT_RESOLVE,
    FONT_HEADING, FONT_HEADING_LG, FONT_SUBHEADING, FONT_BODY, FONT_SMALL,
    FONT_MONO, FONT_BUTTON,
    PAD_S, PAD_M, PAD_L, PAD_XL,
    money_str,
)
from .panes import (
    ActionsPanel, FinancePanel, LifePanel, LogPanel, OutlookPanel,
    ScoreStrip, StatusBar, build_menu_bar,
    show_milestone_popup, show_endgame_popup,
)


@dataclass
class _SetupGroup:
    key: str
    title: str
    prompt: str
    options: list[tuple[str, str, str]]
    initial_id: str | None


@dataclass(frozen=True)
class BuildSystemVM:
    system: str
    primary: str
    detail: str | None = None
    tone: str = "neutral"

    @property
    def label(self) -> str:
        return self.system

    @property
    def value(self) -> str:
        return self.primary


@dataclass(frozen=True)
class BuildSnapshotVM:
    player_name: str
    city_name: str
    items: list[BuildSystemVM] = field(default_factory=list)

    @property
    def headline(self) -> str:
        return f"{self.player_name} in {self.city_name}"

    @property
    def systems(self) -> list[BuildSystemVM]:
        return self.items


@dataclass(frozen=True)
class MonthlyForecastVM:
    monthly_focus: str
    main_threat: str
    best_opportunity: str
    chosen_focus: str
    expected_swing: str
    driver_notes: list[str] = field(default_factory=list)
    recent_summary: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PressureMetricVM:
    label: str
    primary: str
    detail: str | None = None
    tone: str = "neutral"


@dataclass(frozen=True)
class PressureSummaryVM:
    projected_score: float
    score_tier: str
    biggest_risk: str
    primary_metrics: list[PressureMetricVM] = field(default_factory=list)
    secondary_metrics: list[PressureMetricVM] = field(default_factory=list)
    active_modifiers: list[str] = field(default_factory=list)
    crisis_watch: list[str] = field(default_factory=list)

    @property
    def tier(self) -> str:
        return self.score_tier


@dataclass(frozen=True)
class ScoreDeltaVM:
    previous_score: float | None
    current_score: float
    delta: float
    previous_tier: str | None
    tier: str
    strongest_category: str
    weakest_category: str
    diagnosis: str

    @property
    def prev_score(self) -> float | None:
        return self.previous_score

    @property
    def prev_tier(self) -> str | None:
        return self.previous_tier


def _lookup_option(options: list[tuple[str, str, str]], value_id: str | None) -> tuple[str, str, str]:
    if value_id is not None:
        for option in options:
            if option[1] == value_id:
                return option
    return options[0]


def _money(value: int) -> str:
    return f"${value:,}"


@dataclass(frozen=True)
class _Context:
    state: object
    bundle: object


def _resolve_context(source, bundle=None) -> _Context:
    if bundle is None and hasattr(source, "state") and hasattr(source, "bundle"):
        return _Context(state=source.state, bundle=source.bundle)
    if bundle is not None:
        return _Context(state=source, bundle=bundle)
    raise TypeError("Expected a controller or a (state, bundle) pair.")


def _find_label(options: list, value_id: str, default: str = "") -> str:
    for option in options:
        if option.id == value_id:
            return option.name
    return default


def _current_focus_name(controller) -> str:
    player = controller.state.player
    return _find_label(controller.bundle.focus_actions, player.selected_focus_action_id, "Focus")


def _current_focus_description(controller) -> str:
    player = controller.state.player
    for option in controller.bundle.focus_actions:
        if option.id == player.selected_focus_action_id:
            return option.description
    return "Choose a monthly focus."


def _current_career_tier_label(controller) -> str:
    state = controller.state
    track = next(track for track in controller.bundle.careers if track.id == state.player.career.track_id)
    return track.tiers[state.player.career.tier_index].label


def _current_career_track_name(controller) -> str:
    state = controller.state
    track = next(track for track in controller.bundle.careers if track.id == state.player.career.track_id)
    return track.name


def _current_city(controller) -> str:
    city = next(item for item in controller.bundle.cities if item.id == controller.state.player.current_city_id)
    return city.name


def _build_crisis_warnings(state, bundle) -> list[str]:
    player = state.player
    warnings: list[str] = []
    if player.debt >= state.debt_game_over_threshold * bundle.config.crisis_warning_debt_ratio:
        warnings.append("Debt is getting close to collections.")
    if player.stress >= bundle.config.crisis_warning_stress:
        warnings.append("Stress is getting close to burnout territory.")
    if player.energy <= bundle.config.crisis_warning_energy:
        warnings.append("Energy is dangerously low.")
    if player.energy < 30:
        warnings.append("Energy is capping your income - overtime and gig hours are unreliable.")
    if player.housing.missed_payment_streak >= bundle.config.crisis_warning_housing_streak:
        warnings.append("Housing stability is wobbling.")
    if player.education.failure_streak >= max(1, state.academic_failure_streak_limit - 1):
        warnings.append("School pressure is close to a hard setback.")
    if player.housing.housing_stability <= 40:
        warnings.append("Housing stability is sliding and may cascade into stress.")
    if player.transport.reliability_score <= 45:
        warnings.append("Transport reliability is now threatening your work consistency.")
    if player.career.transition_penalty_months > 0:
        warnings.append("Career transition drag is still active.")
    if player.social_stability <= 35:
        warnings.append("Social isolation is dragging down recovery and performance.")
    if player.social_stability > 80:
        current_year = ((state.current_month - 1) // 12) + 1
        if player.last_social_lifeline_year < current_year:
            warnings.append("Your strong network can bail you out once this year if things go bad.")
    if state.pending_events:
        warnings.append(f"Something is building - {len(state.pending_events)} consequence(s) pending.")
    return warnings


def _build_month_outlook_lines(state, bundle) -> list[str]:
    player = state.player
    city = next(item for item in bundle.cities if item.id == player.current_city_id)
    focus_name = _find_label(bundle.focus_actions, player.selected_focus_action_id, "Focus")
    outlook = [
        f"{city.name}: {city.opportunity_text}",
        f"Pressure: {city.pressure_text}",
        f"Current lane: {player.career.track_id.replace('_', ' ').title()}.",
        f"Focus: {focus_name}.",
    ]
    outlook.extend(_build_crisis_warnings(state, bundle))
    return outlook


def _best_breakdown_category(breakdown: dict[str, float], *, reverse: bool) -> str:
    labels = {
        "net_worth": "Net Worth",
        "monthly_surplus": "Cash Flow",
        "debt_ratio": "Debt",
        "career_tier": "Career",
        "credentials_education": "Education",
        "housing_stability": "Housing",
        "life_satisfaction": "Life",
        "stress_burnout": "Wellness",
    }
    key = max(breakdown, key=breakdown.get) if reverse else min(breakdown, key=breakdown.get)
    return labels.get(key, key.replace("_", " ").title())


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
    stance = next(item for item in controller.bundle.config.budget_stances if item.id == player.budget_stance_id)
    wealth = next(item for item in controller.bundle.wealth_strategies if item.id == player.wealth_strategy_id)
    focus_name = _current_focus_name(controller)
    systems = [
        BuildSystemVM("Career", current_tier.label, f"{career_track.name} | momentum {player.career.promotion_momentum}", "career"),
        BuildSystemVM("Education", education.name, f"{'Active' if player.education.is_active else 'Paused'} | {player.education.intensity_level.title()}", "education"),
        BuildSystemVM("Housing", housing.name, f"{player.housing.housing_stability}/100 stability", "housing"),
        BuildSystemVM("Transport", transport.name, f"{player.transport.reliability_score}/100 reliability", "transport"),
        BuildSystemVM("Budget", stance.name, f"Cash flow stance: {_money(player.monthly_surplus)}", "budget"),
        BuildSystemVM("Wealth", wealth.name, f"Portfolio: {_money(player.high_interest_savings + player.index_fund + player.aggressive_growth_fund)}", "wealth"),
        BuildSystemVM("Focus", focus_name, _current_focus_description(controller), "focus"),
    ]
    return BuildSnapshotVM(player_name=player.name, city_name=city.name, items=systems)


def build_monthly_forecast_vm(source, bundle=None) -> MonthlyForecastVM:
    controller = _resolve_context(source, bundle)
    state = controller.state
    player = state.player
    focus_name = _current_focus_name(controller)
    focus_description = _current_focus_description(controller)
    warnings = _build_crisis_warnings(state, controller.bundle)
    city = next(item for item in controller.bundle.cities if item.id == player.current_city_id)
    main_threat = warnings[0] if warnings else (city.pressure_text or "No major threat is pressing right now.")
    best_opportunity = city.opportunity_text
    expected_swing = f"Projected monthly swing {_money(player.monthly_surplus)} before pressure"
    recent_summary = list(state.recent_summary[:3])
    driver_notes = list(state.month_driver_notes[:5])
    if not recent_summary:
        recent_summary = _build_month_outlook_lines(state, controller.bundle)[-2:]
    return MonthlyForecastVM(
        monthly_focus=focus_description,
        main_threat=main_threat,
        best_opportunity=best_opportunity,
        chosen_focus=focus_name,
        expected_swing=expected_swing,
        driver_notes=driver_notes,
        recent_summary=recent_summary,
    )


def build_pressure_summary_vm(source, bundle=None, snapshot: LiveScoreSnapshot | None = None) -> PressureSummaryVM:
    controller = _resolve_context(source, bundle)
    state = controller.state
    player = state.player
    snapshot = snapshot or build_live_score_snapshot(controller.bundle, state)
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
    return PressureSummaryVM(
        projected_score=snapshot.projected_score,
        score_tier=snapshot.score_tier,
        biggest_risk=snapshot.biggest_risk,
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


def build_setup_summary_lines(bundle, selections: dict[str, str], player_name: str) -> list[str]:
    preset = next(item for item in bundle.presets if item.id == selections["preset_id"])
    city = next(item for item in bundle.cities if item.id == selections["city_id"])
    academic = next(item for item in bundle.config.academic_levels if item.id == selections["academic_level_id"])
    support = next(item for item in bundle.config.family_support_levels if item.id == selections["family_support_level_id"])
    savings = next(item for item in bundle.config.savings_bands if item.id == selections["savings_band_id"])
    path = next(item for item in bundle.config.opening_paths if item.id == selections["opening_path_id"])
    difficulty = next(item for item in bundle.difficulties if item.id == selections["difficulty_id"])
    opening_cash = preset.starting_cash + savings.cash_delta
    opening_savings = preset.starting_savings + savings.savings_delta
    opening_debt = preset.starting_debt + savings.debt_delta
    opening_net = opening_cash + opening_savings - opening_debt
    tags: list[str] = []
    if opening_net >= 0:
        tags.append("Safe Start")
    if opening_debt > opening_cash + opening_savings:
        tags.append("Debt Risk")
    if support.name.lower() in {"high", "strong", "best", "excellent"} or support.description.lower().find("family") >= 0:
        tags.append("Beginner Friendly")
    if academic.name.lower() in {"average", "strong", "excellent"}:
        tags.append("High Upside")
    if not tags:
        tags.append("Rough Start")
    forecast = "You can likely absorb a mistake early." if opening_net >= 0 else "You will need to protect cash flow early."
    return [
        f"Player: {player_name or 'Player'}",
        "",
        "Opening Identity",
        "Your Start",
        f"Preset: {preset.name}",
        f"City: {city.name}",
        "",
        "Opening Lane",
        "Your Pressure",
        f"Path: {path.name}",
        f"Academics: {academic.name}",
        f"Family support: {support.name}",
        f"Starting cushion: {savings.name}",
        "",
        "Run Preview",
        "Your Best Edge",
        f"Cash: {_money(opening_cash)} | Savings: {_money(opening_savings)} | Debt: {_money(opening_debt)}",
        f"Opening net worth: {_money(opening_net)}",
        f"Forecast: {forecast}",
        f"Tags: {', '.join(tags)}",
        f"Difficulty: {difficulty.name}",
    ]


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
            selectbackground=ACCENT_RESOLVE, selectforeground=BG_DARKEST,
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
        self._group_vars: dict[str, tk.StringVar] = {}
        self._group_desc_vars: dict[str, tk.StringVar] = {}
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
        super().__init__(parent, "Start New Run")

    def body(self, master: tk.Misc):
        master.configure(bg=BG_DARKEST)
        self.configure(bg=BG_DARKEST)
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
        canvas.create_window((0, 0), window=options_frame, anchor="nw")
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
            self._group_vars[group.key] = var
            self._group_desc_vars[group.key] = desc_var

            frame = tk.LabelFrame(options_frame, text=group.title, padx=PAD_M, pady=PAD_S,
                                  bg=BG_ELEVATED, fg=TEXT_HEADING, font=FONT_SMALL,
                                  bd=0, relief="flat")
            frame.grid(row=row, column=0, sticky="ew", pady=3)
            frame.columnconfigure(0, weight=1)

            combo = ttk.Combobox(frame, values=option_labels, textvariable=var, state="readonly")
            combo.grid(row=0, column=0, sticky="ew")
            combo.bind("<<ComboboxSelected>>", lambda _event, key=group.key: self._sync_group_description(key))

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
            font=FONT_MONO, spacing1=1, spacing3=2,
            insertbackground=BG_ELEVATED,
        )
        self.summary_text.grid(row=0, column=0, sticky="nsew")
        self.summary_text.configure(state="disabled")

        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = min(max(1100, int(screen_w * 0.9)), max(960, screen_w - 40))
        height = min(max(700, int(screen_h * 0.9)), max(660, screen_h - 40))
        self.geometry(f"{width}x{height}")
        self.minsize(min(1100, max(960, screen_w - 120)), min(700, max(660, screen_h - 120)))

        self._refresh_summary()
        return self.name_entry

    def _sync_group_description(self, key: str) -> None:
        option = self._current_option(key)
        self._group_desc_vars[key].set(option[2])
        self._refresh_summary()

    def _current_option(self, key: str) -> tuple[str, str, str]:
        selected_label = self._group_vars[key].get()
        return self._value_maps[key][selected_label]

    def _selected_ids(self) -> dict[str, str]:
        return {key: self._current_option(key)[1] for key in self._group_vars}

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
        self._previous_snapshot = None
        self._latest_snapshot = None
        self.pack(fill="both", expand=True)
        self._build_layout()
        self._apply_text_scale()
        self.refresh()

    @property
    def controller(self):
        return self.session.require_controller()

    def _build_layout(self) -> None:
        # ── Status bar (top) ──
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill="x", padx=PAD_M, pady=(PAD_M, PAD_S))

        # ── Score strip ──
        self.score_strip = ScoreStrip(self, on_click=self.show_score_projection)
        self.score_strip.pack(fill="x", padx=PAD_M, pady=(0, PAD_S))

        # ── Main content area ──
        content = tk.Frame(self, bg=BG_DARKEST)
        content.pack(fill="both", expand=True, padx=PAD_M, pady=(0, PAD_S))

        # Left: life panel
        self.life_panel = LifePanel(content, "Build")
        self.life_panel.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_S))

        # Center: outlook + log
        center = tk.Frame(content, bg=BG_DARKEST)
        center.grid(row=0, column=1, sticky="nsew", padx=PAD_S)
        self.outlook_panel = OutlookPanel(center, "This Month")
        self.outlook_panel.pack(fill="both", expand=True, pady=(0, PAD_S))
        self.log_panel = LogPanel(center, "Run Feedback")
        self.log_panel.pack(fill="both", expand=True)

        # Right: finance panel
        self.finance_panel = FinancePanel(content, "Score & Pressure")
        self.finance_panel.grid(row=0, column=2, sticky="nsew", padx=(PAD_S, 0))

        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=4)
        content.grid_columnconfigure(2, weight=3)
        content.grid_rowconfigure(0, weight=1)

        # ── Actions bar (bottom) ──
        self.actions_panel = ActionsPanel(self)
        self.actions_panel.pack(fill="x", padx=PAD_M, pady=(0, PAD_M))
        self.actions_panel.set_grouped_actions(self._build_action_groups())

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
                    "score": self.show_score_projection,
                    "help": self.show_help,
                },
            )
        )

    def _choose(self, title: str, prompt: str, options: list[tuple[str, str, str]]) -> str | None:
        if not options:
            messagebox.showinfo(title, "No valid options right now.")
            return None
        dialog = SelectionDialog(self.master, title, prompt, options)
        return dialog.result

    def _build_action_groups(self) -> list[tuple[str, list[tuple[str, object]]]]:
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
            ("This Month", [
                ("Focus", self.change_focus),
                ("Resolve Month", self.resolve_month),
            ]),
        ]

    def _auto_save(self) -> None:
        self.session.autosave()

    def _after_action(self) -> None:
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
            "",
            f"Main threat: {vm.main_threat}",
            f"Best opportunity: {vm.best_opportunity}",
            f"Expected swing: {vm.expected_swing}",
        ]
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
            f"Strongest category: {delta_vm.strongest_category}",
            f"Weakest category: {delta_vm.weakest_category}",
            f"Biggest Risk: {vm.biggest_risk}",
            "",
        ]
        lines.extend(f"{metric.label}: {metric.primary}" for metric in vm.primary_metrics)
        lines.append("")
        lines.extend(f"{metric.label}: {metric.primary}" for metric in vm.secondary_metrics[:5])
        lines.append("")
        lines.append("Active Modifiers:")
        lines.append(", ".join(vm.active_modifiers) if vm.active_modifiers else "None")
        lines.append("")
        lines.append("Crisis Watch:")
        lines.extend(vm.crisis_watch or ["Stable enough for now."])
        return lines

    def refresh(self) -> None:
        state = self.controller.state
        self._previous_snapshot = self._latest_snapshot
        self._latest_snapshot = self.controller.live_score_snapshot()
        delta_vm = build_score_delta_vm(self._previous_snapshot, self._latest_snapshot)
        self.status_bar.render(state, self.controller.bundle, self._latest_snapshot)
        self.score_strip.render(self._latest_snapshot, delta_vm)
        self.life_panel.render_snapshot(build_build_snapshot_vm(self.controller))
        self.outlook_panel.render_forecast(build_monthly_forecast_vm(self.controller))
        self.finance_panel.render_summary(build_pressure_summary_vm(self.controller, snapshot=self._latest_snapshot), delta_vm)
        self.log_panel.render(self._run_feedback_lines(), limit=10)
        size_tag = "Large Text" if self._large_text else "Normal Text"
        self.master.title(f"{state.game_title} - {state.player.name} ({size_tag})")

    def _run_feedback_lines(self) -> list[str]:
        state = self.controller.state
        crisis = self.controller.build_crisis_warnings()
        next_best_move = _current_focus_name(self.controller)
        return [
            f"Big Win: {state.recent_summary[0]}" if state.recent_summary else "Big Win: Holding steady.",
            f"Big Hit: {state.recent_summary[1]}" if len(state.recent_summary) > 1 else "Big Hit: No major hit this month.",
            f"Score Change: {self._latest_snapshot.projected_score:.1f}" if self._latest_snapshot else "Score Change: Pending.",
            f"New Threat: {crisis[0]}" if crisis else "New Threat: None right now.",
            f"Next Best Move: {next_best_move}",
        ] + state.log_messages

    def _apply_text_scale(self) -> None:
        self.status_bar.set_large_text(self._large_text)
        self.life_panel.set_large_text(self._large_text)
        self.outlook_panel.set_large_text(self._large_text)
        self.finance_panel.set_large_text(self._large_text)
        self.log_panel.set_large_text(self._large_text)
        self.actions_panel.set_large_text(self._large_text)
        self.score_strip.set_large_text(self._large_text)

    def toggle_large_text(self) -> None:
        self._large_text = not self._large_text
        self._apply_text_scale()
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
        self._after_action()

    def change_career(self) -> None:
        options: list[tuple[str, str, str]] = []
        for name, track_id, allowed, reason in self.controller.career_entry_statuses():
            if not allowed:
                continue
            description = next(track.description for track in self.controller.bundle.careers if track.id == track_id)
            options.append((name, track_id, description))
        chosen = self._choose("Career", "Choose your career lane:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_career(chosen))

    def change_education(self) -> None:
        options = [(program.name, program.id, program.description) for program in self.controller.available_education_programs()]
        chosen = self._choose("Education", "Choose your education plan. Picking the current plan toggles pause/resume.", options)
        if chosen:
            if chosen != "none":
                intensity = self._choose(
                    "Education Intensity", 
                    "How hard are you pushing this month?", 
                    [
                        ("Standard", "standard", "Normal pace and stress (1.0x)."), 
                        ("Intensive", "intensive", "Higher cost, higher stress, better GPA trend (1.3x, 1.5x)."), 
                        ("Light", "light", "Lower cost, lower stress, risk of slipping GPA (0.7x, 0.5x).")
                    ]
                )
                if intensity:
                    self._run_action(lambda: self.controller.change_education(chosen, intensity))
            else:
                self._run_action(lambda: self.controller.change_education(chosen))

    def change_housing(self) -> None:
        options = [
            (f"{option.name} | move {_money(option.move_in_cost)}", option.id, option.description)
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
            options.append((f"{option.name} | upfront {_money(upfront)} | monthly {_money(monthly)}", option.id, option.description))
        chosen = self._choose("Transport", "Choose your transport setup:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_transport(chosen))

    def change_budget(self) -> None:
        options = [(stance.name, stance.id, stance.description) for stance in self.controller.available_budget_stances()]
        chosen = self._choose("Budget", "Choose your monthly budget stance:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_budget_stance(chosen))

    def change_wealth(self) -> None:
        options = [(strategy.name, strategy.id, strategy.description) for strategy in self.controller.available_wealth_strategies()]
        chosen = self._choose("Wealth Strategy", "Choose how you want extra money to behave each month:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_wealth_strategy(chosen))

    def change_focus(self) -> None:
        options = [(focus.name, focus.id, focus.description) for focus in self.controller.available_focus_actions()]
        chosen = self._choose("Focus", "Choose this month's focus:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_focus_action(chosen))

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
            "The goal is to chase the strongest score you can build before age 28.",
        )
