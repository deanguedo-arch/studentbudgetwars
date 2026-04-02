from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

from budgetwars.core import GameSession, StartupOptions

from .panes import ActionsPanel, FinancePanel, LifePanel, LogPanel, StatusBar, build_menu_bar


class SelectionDialog(simpledialog.Dialog):
    def __init__(self, parent: tk.Misc, title: str, prompt: str, options: list[tuple[str, str, str]]):
        self.prompt = prompt
        self.options = options
        self.result: str | None = None
        self._desc_var = tk.StringVar(value="")
        super().__init__(parent, title)

    def body(self, master: tk.Misc):
        tk.Label(master, text=self.prompt, justify="left", wraplength=540, font=("Segoe UI", 10, "bold")).pack(
            anchor="w", padx=6, pady=(6, 2)
        )
        self.listbox = tk.Listbox(master, width=56, height=min(9, max(4, len(self.options))))
        self.listbox.configure(font=("Segoe UI", 11))
        self.listbox.pack(fill="both", expand=True, padx=6, pady=6)
        for label, _, _ in self.options:
            self.listbox.insert("end", label)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        tk.Label(
            master,
            textvariable=self._desc_var,
            justify="left",
            anchor="w",
            wraplength=540,
            bg="#f0f0f0",
            relief="sunken",
            bd=1,
            padx=6,
            pady=5,
            font=("Segoe UI", 10),
        ).pack(fill="x", padx=6, pady=(0, 6))
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
    preset_options = [(preset.name, preset.id, preset.description) for preset in bundle.presets]
    city_options = [(city.name, city.id, city.opportunity_text) for city in bundle.cities]
    academic_options = [(option.name, option.id, option.description) for option in bundle.config.academic_levels]
    support_options = [(option.name, option.id, option.description) for option in bundle.config.family_support_levels]
    savings_options = [(option.name, option.id, option.description) for option in bundle.config.savings_bands]
    path_options = [(path.name, path.id, path.description) for path in bundle.config.opening_paths]
    difficulty_options = [(difficulty.name, difficulty.id, difficulty.description) for difficulty in bundle.difficulties]

    preset_id = initial_preset_id or SelectionDialog(parent, "Choose Preset", "Choose the background you are starting from:", preset_options).result
    if not preset_id:
        return None
    city_id = initial_city_id or SelectionDialog(parent, "Choose City", "Choose the kind of city you are entering adulthood in:", city_options).result
    if not city_id:
        return None
    academic_level_id = initial_academic_level_id or SelectionDialog(parent, "Academics", "How strong is your academic footing?", academic_options).result
    if not academic_level_id:
        return None
    family_support_level_id = initial_family_support_level_id or SelectionDialog(parent, "Family Support", "How much backup do you realistically have?", support_options).result
    if not family_support_level_id:
        return None
    savings_band_id = initial_savings_band_id or SelectionDialog(parent, "Starting Cushion", "How much cushion are you really starting with?", savings_options).result
    if not savings_band_id:
        return None
    opening_path_id = initial_opening_path_id or SelectionDialog(parent, "Opening Path", "Pick the first lane you are stepping into:", path_options).result
    if not opening_path_id:
        return None
    difficulty_id = initial_difficulty_id or SelectionDialog(parent, "Difficulty", "Pick how hard the decade should hit back:", difficulty_options).result
    if not difficulty_id:
        return None
    player_name = simpledialog.askstring("Player Name", "Name:", initialvalue=initial_name, parent=parent)
    if player_name is None:
        return None
    return {
        "player_name": player_name or "Player",
        "preset_id": preset_id,
        "city_id": city_id,
        "academic_level_id": academic_level_id,
        "family_support_level_id": family_support_level_id,
        "savings_band_id": savings_band_id,
        "opening_path_id": opening_path_id,
        "difficulty_id": difficulty_id,
    }


class MainWindow(tk.Frame):
    def __init__(self, master: tk.Tk, session: GameSession):
        super().__init__(master, bg="#c0c0c0")
        self.master = master
        self.session = session
        self._result_announced = False
        self._shown_milestone_count = 0
        self._large_text = False
        self.pack(fill="both", expand=True)
        self._build_layout()
        self._apply_text_scale()
        self.refresh()

    @property
    def controller(self):
        return self.session.require_controller()

    def _build_layout(self) -> None:
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill="x", padx=6, pady=(6, 4))

        content = tk.Frame(self, bg="#c0c0c0")
        content.pack(fill="both", expand=True, padx=6, pady=(0, 4))

        self.life_panel = LifePanel(content, "Current Life Setup")
        self.life_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        center = tk.Frame(content, bg="#c0c0c0")
        center.grid(row=0, column=1, sticky="nsew", padx=4)
        self.outlook_panel = LifePanel(center, "Month Outlook")
        self.outlook_panel.pack(fill="both", expand=True, pady=(0, 4))
        self.log_panel = LogPanel(center, "Recent Activity")
        self.log_panel.pack(fill="both", expand=True)

        self.finance_panel = FinancePanel(content, "Finances, Progress, and Pressure")
        self.finance_panel.grid(row=0, column=2, sticky="nsew", padx=(4, 0))

        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=4)
        content.grid_columnconfigure(2, weight=3)
        content.grid_rowconfigure(0, weight=1)

        self.actions_panel = ActionsPanel(self)
        self.actions_panel.pack(fill="x", padx=6, pady=(0, 6))
        self.actions_panel.set_actions(
            [
                ("Career", self.change_career),
                ("Education", self.change_education),
                ("Housing", self.change_housing),
                ("Transport", self.change_transport),
                ("Budget", self.change_budget),
                ("Wealth", self.change_wealth),
                ("Focus", self.change_focus),
                ("Resolve Month", self.resolve_month),
                ("Save", self.save_game),
            ]
        )

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
        state = self.controller.state
        player = state.player
        career_track = next(track for track in self.controller.bundle.careers if track.id == player.career.track_id)
        current_tier = career_track.tiers[player.career.tier_index]
        education = next(program for program in self.controller.bundle.education_programs if program.id == player.education.program_id)
        housing = next(item for item in self.controller.bundle.housing_options if item.id == player.housing_id)
        transport = next(item for item in self.controller.bundle.transport_options if item.id == player.transport_id)
        city = next(item for item in self.controller.bundle.cities if item.id == player.current_city_id)
        stance = next(item for item in self.controller.bundle.config.budget_stances if item.id == player.budget_stance_id)
        focus = next(item for item in self.controller.bundle.focus_actions if item.id == player.selected_focus_action_id)
        wealth = next(item for item in self.controller.bundle.wealth_strategies if item.id == player.wealth_strategy_id)
        return [
            f"Name: {player.name}",
            f"City: {city.name}",
            f"Path: {player.opening_path_id.replace('_', ' ').title()}",
            "",
            f"Career: {career_track.name}",
            f"Tier: {current_tier.label}",
            f"Promotion Progress: {player.career.promotion_progress}",
            f"Career Momentum: {player.career.promotion_momentum}",
            f"Transition Drag: {player.career.transition_penalty_months}m",
            "",
            f"Education: {education.name}",
            f"Active: {'Yes' if player.education.is_active else 'No'}",
            f"Paused: {'Yes' if player.education.is_paused else 'No'}",
            f"Progress: {player.education.months_completed}/{education.duration_months or 0}",
            f"Standing: {player.education.standing}",
            f"Edu Momentum: {player.education.education_momentum}",
            (
                f"GPA: {player.education.college_gpa:.2f}"
                if education.uses_gpa
                else f"Passed: {'Yes' if player.education.training_passed else 'No'}"
            ),
            f"Credentials: {', '.join(player.education.earned_credential_ids) or 'None'}",
            "",
            f"Housing: {housing.name}",
            f"Months There: {player.housing.months_in_place}",
            f"Housing Stability: {player.housing.housing_stability}",
            f"Transport: {transport.name}",
            f"Transport Reliability: {player.transport.reliability_score}",
            f"Budget: {stance.name}",
            f"Wealth: {wealth.name}",
            f"Focus: {focus.name}",
        ]

    def _outlook_lines(self) -> list[str]:
        outlook = self.controller.build_month_outlook()
        if self.controller.state.month_driver_notes:
            outlook = outlook + ["", "Why This Month Changed:"] + self.controller.state.month_driver_notes
        summary = self.controller.state.recent_summary
        if summary:
            outlook = outlook + ["", "Last Month Summary:"] + summary
        return outlook

    def _finance_lines(self) -> list[str]:
        state = self.controller.state
        player = state.player
        housing = next(item for item in self.controller.bundle.housing_options if item.id == player.housing_id)
        transport = next(item for item in self.controller.bundle.transport_options if item.id == player.transport_id)
        wealth = next(item for item in self.controller.bundle.wealth_strategies if item.id == player.wealth_strategy_id)
        modifiers = ", ".join(f"{modifier.label} ({modifier.remaining_months})" for modifier in state.active_modifiers) or "None"
        warnings = self.controller.build_crisis_warnings()
        return [
            f"Cash: ${player.cash}",
            f"Savings: ${player.savings}",
            f"High-Interest: ${player.high_interest_savings}",
            f"Index Fund: ${player.index_fund}",
            f"Growth Fund: ${player.aggressive_growth_fund}",
            f"Debt: ${player.debt}",
            f"Income: ${player.monthly_income}",
            f"Expenses: ${player.monthly_expenses}",
            f"Monthly Swing: {player.monthly_surplus:+d}",
            "",
            f"Stress: {player.stress}/{state.max_stress}",
            f"Energy: {player.energy}/{state.max_energy}",
            f"Life Satisfaction: {player.life_satisfaction}/{state.max_life_satisfaction}",
            f"Family Support: {player.family_support}/{state.max_family_support}",
            f"Social Stability: {player.social_stability}/{state.max_social_stability}",
            "",
            f"Housing Quality: {housing.quality_score}",
            f"Transport Access: {transport.access_level}",
            f"Housing Risk: {player.housing.missed_payment_streak}/{state.housing_miss_limit}",
            f"Housing Stability: {player.housing.housing_stability}/100",
            f"Burnout Streak: {state.burnout_streak}/{state.burnout_streak_limit}",
            f"School Failure Streak: {player.education.failure_streak}/{state.academic_failure_streak_limit}",
            f"Transport Reliability: {player.transport.reliability_score}/100",
            f"Market Regime: {state.current_market_regime_id.replace('_', ' ').title()}",
            f"Wealth Strategy: {wealth.name}",
            "",
            "Active Modifiers:",
            modifiers,
            "",
            "Crisis Watch:",
            *(warnings or ["Stable enough for now."]),
        ]

    def refresh(self) -> None:
        state = self.controller.state
        self.status_bar.render(state, self.controller.bundle)
        self.life_panel.render(self._life_lines())
        self.outlook_panel.render(self._outlook_lines())
        self.finance_panel.render(self._finance_lines())
        self.log_panel.render(state.log_messages)
        size_tag = "Large Text" if self._large_text else "Normal Text"
        self.master.title(f"{state.game_title} - {state.player.name} ({size_tag})")

    def _apply_text_scale(self) -> None:
        self.status_bar.set_large_text(self._large_text)
        self.life_panel.set_large_text(self._large_text)
        self.outlook_panel.set_large_text(self._large_text)
        self.finance_panel.set_large_text(self._large_text)
        self.log_panel.set_large_text(self._large_text)
        self.actions_panel.set_large_text(self._large_text)

    def toggle_large_text(self) -> None:
        self._large_text = not self._large_text
        self._apply_text_scale()
        self.refresh()

    def _check_milestones(self) -> None:
        if len(self.controller.state.annual_milestones) <= self._shown_milestone_count:
            return
        latest = self.controller.state.annual_milestones[-1]
        messagebox.showinfo("Annual Milestone", "\n".join(latest.summary_lines))
        self._shown_milestone_count = len(self.controller.state.annual_milestones)

    def _check_end_state(self) -> None:
        if self._result_announced or not self.controller.is_finished():
            return
        summary = self.controller.final_score_summary()
        breakdown = "\n".join(f"{key.replace('_', ' ').title()}: {value:.2f}" for key, value in summary.breakdown.items())
        messagebox.showinfo(
            "Life Position",
            f"{summary.ending_label}\n\n{summary.outcome}\n\nFinal Score: {summary.final_score}\n\n{breakdown}",
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
            self._run_action(lambda: self.controller.change_education(chosen))

    def change_housing(self) -> None:
        options = [
            (f"{option.name} | move ${option.move_in_cost}", option.id, option.description)
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
            options.append((f"{option.name} | upfront ${upfront} | monthly ${monthly}", option.id, option.description))
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
        breakdown = "\n".join(f"{key.replace('_', ' ').title()}: {value:.2f}" for key, value in summary.breakdown.items())
        messagebox.showinfo(
            "Projected Ending",
            f"{summary.ending_label}\nScore: {summary.final_score}\n\n{summary.outcome}\n\n{breakdown}",
        )

    def show_help(self) -> None:
        messagebox.showinfo(
            "How To Play",
            "Each turn is one month.\n\n"
            "Your persistent setup is your career lane, education plan, housing, transport, and budget stance.\n"
            "You also control a separate wealth strategy for liquidity, debt paydown, and investing posture.\n"
            "Pick one monthly focus, then resolve the month and react to the pressure that follows.\n\n"
            "The goal is not just cash. Reach age 28 in the strongest life position you can build.",
        )
