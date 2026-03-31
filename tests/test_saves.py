from budgetwars.game import start_new_game
from budgetwars.saves import load_game, save_game


def test_save_and_load_round_trip(tmp_path) -> None:
    _, state = start_new_game(player_name="Casey", seed=99)
    path = save_game(state, "test-save.json", saves_dir=tmp_path)
    loaded = load_game(path.name, saves_dir=tmp_path)

    assert loaded == state
