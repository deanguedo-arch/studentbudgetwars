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
from .build_snapshot import build_build_snapshot, build_build_snapshot_vm
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
from .dialogs import SelectionDialog, prompt_new_game_setup
from .diagnostics import (
    _active_status_arc_vms,
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
from .monthly_forecast import build_monthly_forecast, build_monthly_forecast_vm
from .pressure_summary import (
    build_pressure_summary,
    build_pressure_summary_vm,
    build_score_delta_summary,
    build_score_delta_vm,
)
from .learn_drawer_builder import build_learn_drawer, build_learn_drawer_vm
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
