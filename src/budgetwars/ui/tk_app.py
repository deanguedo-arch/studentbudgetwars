from __future__ import annotations

import tkinter as tk

from budgetwars.engine import GameController
from budgetwars.models import ContentBundle

from .main_window import MainWindow, prompt_new_game_setup


class BudgetWarsTkApp:
    def __init__(
        self,
        bundle: ContentBundle,
        controller: GameController | None = None,
        *,
        player_name: str = "Player",
        preset_id: str | None = None,
        difficulty_id: str | None = None,
        city_id: str | None = None,
        opening_path_id: str | None = None,
        seed: int | None = None,
    ):
        self.root = tk.Tk()
        self.root.configure(bg="#c0c0c0")
        self.root.geometry("1260x780")
        self.root.minsize(1080, 700)

        if controller is None:
            setup = prompt_new_game_setup(
                self.root,
                bundle,
                initial_name=player_name,
                initial_preset_id=preset_id,
                initial_city_id=city_id,
                initial_opening_path_id=opening_path_id,
                initial_difficulty_id=difficulty_id,
            )
            if not setup:
                self.root.destroy()
                raise SystemExit(0)
            controller = GameController.new_game(
                bundle,
                player_name=setup["player_name"],
                preset_id=setup["preset_id"],
                difficulty_id=setup["difficulty_id"],
                city_id=setup["city_id"],
                opening_path_id=setup["opening_path_id"],
                seed=seed,
            )
        self.window = MainWindow(self.root, controller)

    def run(self) -> None:
        self.root.mainloop()
