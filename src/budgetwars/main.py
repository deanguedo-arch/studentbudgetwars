from __future__ import annotations

import argparse

from rich.console import Console

from .loaders import load_all_content
from .game import load_existing_game, run_game_loop, start_new_game


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Student Budget Wars")
    parser.add_argument("--load", help="Load a saved game file from the saves directory.")
    parser.add_argument("--name", default="Player", help="Player name for a new game.")
    parser.add_argument("--preset", help="Preset id for a new game.")
    parser.add_argument("--difficulty", default="normal", help="Difficulty id for a new game.")
    parser.add_argument("--seed", type=int, help="Optional random seed override.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    console = Console()

    if args.load:
        state = load_existing_game(args.load)
        bundle = load_all_content()
        run_game_loop(state, bundle=bundle, console=console)
        return

    bundle = load_all_content()
    _, state = start_new_game(
        player_name=args.name,
        preset_id=args.preset,
        difficulty_id=args.difficulty,
        seed=args.seed,
        bundle=bundle,
    )
    run_game_loop(state, bundle=bundle, console=console)


if __name__ == "__main__":
    main()
