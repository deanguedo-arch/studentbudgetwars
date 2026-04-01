from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

from budgetwars.engine import GameController
from budgetwars.loaders import load_all_content
from budgetwars.saves import default_paths, save_named_game

from .panes import ActionsPanel, FinancePanel, LifePanel, LogPanel, StatusBar, build_menu_bar


class SelectionDialog(simpledialog.Dialog):
    def __init__(self, parent: tk.Misc, title: str, prompt: str, options: list[tuple[str, str]]):
        self.prompt = prompt
        self.options = options
        self.result: str | None = None
        super().__init__(parent, title)

    def body(self, master: tk.Misc):
        tk.Label(master, text=self.prompt, justify="left").pack(anchor="w", padx=6, pady=(6, 2))
        self.listbox = tk.Listbox(master, width=56, height=min(10, max(4, len(self.options))))
        self.listbox.pack(fill="both", expand=True, padx=6, pady=6)
        for label, _ in self.options:
            self.listbox.insert("end", label)
        if self.options:
            self.listbox.selection_set(0)
        return self.listbox

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
    initial_opening_path_id: str | None = None,
    initial_difficulty_id: str | None = None,
) -> dict[str, str] | None:
    preset_options = [(preset.name, preset.id) for preset in bundle.presets]
    city_options = [(city.name, city.id) for city in bundle.cities]
    path_options = [(path.name, path.id) for path in bundle.config.opening_paths]
    difficulty_options = [(difficulty.name, difficulty.id) for difficulty in bundle.difficulties]

    preset_id = initial_preset_id or SelectionDialog(parent, "Choose Preset", "Pick your starting background:", preset_options).result
    if not preset_id:
        return None
    city_id = initial_city_id or SelectionDialog(parent, "Choose City", "Pick your city archetype:", city_options).result
    if not city_id:
        return None
    opening_path_id = initial_opening_path_id or SelectionDialog(parent, "Choose Path", "Pick your opening life path:", path_options).result
    if not opening_path_id:
        return None
    difficulty_id = initial_difficulty_id or SelectionDialog(parent, "Difficulty", "Pick a difficulty:", difficulty_options).result
    if not difficulty_id:
        return None
    player_name = simpledialog.askstring("Player Name", "Name:", initialvalue=initial_name, parent=parent)
    if player_name is None:
        return None
    return {
        "player_name": player_name or "Player",
        "preset_id": preset_id,
        "city_id": city_id,
        "opening_path_id": opening_path_id,
        "difficulty_id": difficulty_id,
    }


class MainWindow(tk.Frame):
    def __init__(self, master: tk.Tk, controller: GameController):
        super().__init__(master, bg="#c0c0c0")
        self.master = master
        self.controller = controller
        self.paths = default_paths()
        self._result_announced = False
        self.pack(fill="both", expand=True)
        self._build_layout()
        self.refresh()

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

        self.finance_panel = FinancePanel(content, "Finances & Progress")
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
                    "focus": self.change_focus,
                    "resolve": self.resolve_month,
                    "score": self.show_score_projection,
                    "help": self.show_help,
                },
            )
        )

    def _choose(self, title: str, prompt: str, options: list[tuple[str, str]]) -> str | None:
        if not options:
            messagebox.showinfo(title, "No valid options right now.")
            return None
        dialog = SelectionDialog(self.master, title, prompt, options)
        return dialog.result

    def _auto_save(self) -> None:
        save_named_game(self.controller.state, self.controller.bundle.config.autosave_name, root=self.paths.root)

    def _after_action(self) -> None:
        self._auto_save()
        self.refresh()
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
        return [
            f"Name: {player.name}",
            f"City: {city.name}",
            f"Opening Path: {player.opening_path_id.replace('_', ' ').title()}",
            "",
            f"Career: {career_track.name}",
            f"Tier: {current_tier.label}",
            f"Promotion Progress: {player.career.promotion_progress}",
            "",
            f"Education: {education.name}",
            f"Active: {'Yes' if player.education.is_active else 'No'}",
            f"School Progress: {player.education.months_completed}/{education.duration_months or 0}",
            f"Standing: {player.education.standing}",
            (
                f"GPA: {player.education.college_gpa:.2f}"
                if education.id == "college" or "college_credential" in player.education.earned_credential_ids
                else f"Training Status: {'Passed' if 'apprenticeship_certificate' in player.education.earned_credential_ids else 'In Progress'}"
            ),
            f"Credentials: {', '.join(player.education.earned_credential_ids) or 'None'}",
            "",
            f"Housing: {housing.name}",
            f"Transport: {transport.name}",
            f"Budget: {stance.name}",
            f"Focus: {focus.name}",
        ]

    def _outlook_lines(self) -> list[str]:
        outlook = self.controller.build_month_outlook()
        summary = self.controller.state.recent_summary
        if summary:
            outlook = outlook + ["", "Last Month Summary:"] + summary
        return outlook

    def _finance_lines(self) -> list[str]:
        state = self.controller.state
        player = state.player
        housing = next(item for item in self.controller.bundle.housing_options if item.id == player.housing_id)
        transport = next(item for item in self.controller.bundle.transport_options if item.id == player.transport_id)
        modifiers = ", ".join(f"{modifier.label} ({modifier.remaining_months})" for modifier in state.active_modifiers) or "None"
        return [
            f"Cash: ${player.cash}",
            f"Savings: ${player.savings}",
            f"Debt: ${player.debt}",
            f"Monthly Swing: {player.monthly_surplus:+d}",
            "",
            f"Stress: {player.stress}/{state.max_stress}",
            f"Energy: {player.energy}/{state.max_energy}",
            f"Life Satisfaction: {player.life_satisfaction}/{state.max_life_satisfaction}",
            f"Family Support: {player.family_support}/{state.max_family_support}",
            f"College GPA: {player.education.college_gpa:.2f}",
            "",
            f"Housing Quality: {housing.quality_score}",
            f"Transport Access: {transport.access_level}",
            f"Missed Housing Payments: {state.missed_housing_payments}/{state.housing_miss_limit}",
            f"Burnout Streak: {state.burnout_streak}/{state.burnout_streak_limit}",
            "",
            "Active Modifiers:",
            modifiers,
        ]

    def refresh(self) -> None:
        state = self.controller.state
        self.status_bar.render(state, self.controller.bundle)
        self.life_panel.render(self._life_lines())
        self.outlook_panel.render(self._outlook_lines())
        self.finance_panel.render(self._finance_lines())
        self.log_panel.render(state.log_messages)
        self.master.title(f"{state.game_title} - {state.player.name}")

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
        bundle = load_all_content(self.paths.root)
        setup = prompt_new_game_setup(self.master, bundle)
        if not setup:
            return
        self.controller = GameController.new_game(
            bundle,
            player_name=setup["player_name"],
            preset_id=setup["preset_id"],
            difficulty_id=setup["difficulty_id"],
            city_id=setup["city_id"],
            opening_path_id=setup["opening_path_id"],
        )
        self._result_announced = False
        self._after_action()

    def change_career(self) -> None:
        options = [(track.name, track.id) for track in self.controller.bundle.careers]
        chosen = self._choose("Career", "Choose your career lane:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_career(chosen))

    def change_education(self) -> None:
        options = [(program.name, program.id) for program in self.controller.bundle.education_programs]
        chosen = self._choose("Education", "Choose your education plan:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_education(chosen))

    def change_housing(self) -> None:
        options = [(f"{option.name} | move ${option.move_in_cost}", option.id) for option in self.controller.bundle.housing_options]
        chosen = self._choose("Housing", "Choose your housing setup:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_housing(chosen))

    def change_transport(self) -> None:
        discount = self.controller.current_transport_switch_discount()
        options = []
        for option in self.controller.bundle.transport_options:
            upfront = max(0, option.upfront_cost - discount)
            options.append((f"{option.name} | upfront ${upfront} | monthly ${option.monthly_cost}", option.id))
        chosen = self._choose("Transport", "Choose your transport setup:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_transport(chosen))

    def change_budget(self) -> None:
        options = [(stance.name, stance.id) for stance in self.controller.bundle.config.budget_stances]
        chosen = self._choose("Budget", "Choose your monthly budget stance:", options)
        if chosen:
            self._run_action(lambda: self.controller.change_budget_stance(chosen))

    def change_focus(self) -> None:
        options = [(focus.name, focus.id) for focus in self.controller.bundle.focus_actions]
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
        save_named_game(self.controller.state, save_name, root=self.paths.root)
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
            "Your persistent setup is your job lane, education plan, housing, transport, and budget stance.\n"
            "Pick one monthly focus, then resolve the month and react to the pressure that follows.\n\n"
            "The goal is not just money. Reach age 28 in the strongest overall position you can build.",
        )
