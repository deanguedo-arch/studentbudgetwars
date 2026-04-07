from __future__ import annotations

import tkinter as tk

from budgetwars.core import GameSession, StartupOptions

from .theme import BG_DARKEST, TEXT_PRIMARY, FONT_BODY
from .main_window import MainWindow, prompt_new_game_setup


class BudgetWarsTkApp:
    def __init__(
        self,
        session: GameSession,
        *,
        startup_options: StartupOptions | None = None,
    ):
        self.session = session
        self.startup_options = startup_options or session.options
        self.root = tk.Tk()
        self.root.configure(bg=BG_DARKEST)
        self.root.geometry("1280x780")
        self.root.minsize(1040, 660)
        self.root.option_add("*Font", FONT_BODY)
        self.root.option_add("*Background", BG_DARKEST)

        if not self.session.has_active_game:
            setup = prompt_new_game_setup(
                self.root,
                self.session.bundle,
                initial_name=self.startup_options.player_name,
                initial_preset_id=self.startup_options.preset_id,
                initial_city_id=self.startup_options.city_id,
                initial_academic_level_id=self.startup_options.academic_level_id,
                initial_family_support_level_id=self.startup_options.family_support_level_id,
                initial_savings_band_id=self.startup_options.savings_band_id,
                initial_opening_path_id=self.startup_options.opening_path_id,
                initial_difficulty_id=self.startup_options.difficulty_id,
            )
            if not setup:
                self.root.destroy()
                raise SystemExit(0)
            self.session.start_new_game(
                StartupOptions(
                    mode="classic",
                    player_name=setup["player_name"],
                    preset_id=setup["preset_id"],
                    difficulty_id=setup["difficulty_id"],
                    city_id=setup["city_id"],
                    academic_level_id=setup["academic_level_id"],
                    family_support_level_id=setup["family_support_level_id"],
                    savings_band_id=setup["savings_band_id"],
                    opening_path_id=setup["opening_path_id"],
                    seed=self.startup_options.seed,
                )
            )
        self.window = MainWindow(self.root, self.session)

    def run(self) -> None:
        self.root.mainloop()
