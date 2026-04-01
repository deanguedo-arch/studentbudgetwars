from __future__ import annotations

from budgetwars.engine import GameController
from budgetwars.loaders import load_all_content
from budgetwars.saves import default_paths, load_game, load_named_game
from budgetwars.ui import BudgetWarsTkApp


def run_app(
    player_name: str = "Player",
    preset_id: str | None = None,
    difficulty_id: str | None = None,
    city_id: str | None = None,
    opening_path_id: str | None = None,
    seed: int | None = None,
    load_name: str | None = None,
) -> None:
    paths = default_paths()
    bundle = load_all_content(paths.root)
    controller: GameController | None
    if load_name:
        save_path = paths.saves_dir / load_name
        if save_path.exists():
            state = load_game(save_path)
        else:
            state = load_named_game(load_name, root=paths.root)
        controller = GameController(bundle, state)
    else:
        controller = None
        if preset_id and difficulty_id and city_id and opening_path_id:
            controller = GameController.new_game(
                bundle,
                player_name=player_name,
                preset_id=preset_id,
                difficulty_id=difficulty_id,
                city_id=city_id,
                opening_path_id=opening_path_id,
                seed=seed,
            )
    BudgetWarsTkApp(
        bundle,
        controller,
        player_name=player_name,
        preset_id=preset_id,
        difficulty_id=difficulty_id,
        city_id=city_id,
        opening_path_id=opening_path_id,
        seed=seed,
    ).run()
