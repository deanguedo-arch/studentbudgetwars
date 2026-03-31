from __future__ import annotations

import argparse

from .app import run_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Student Budget Wars: City Hustle")
    parser.add_argument("--load", help="Load a save file from the saves directory.")
    parser.add_argument("--name", default="Player", help="Player name for a new game.")
    parser.add_argument("--preset", help="Preset id for a new game.")
    parser.add_argument("--difficulty", default="normal", help="Difficulty id for a new game.")
    parser.add_argument("--seed", type=int, help="Optional deterministic seed.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_app(
        player_name=args.name,
        preset_id=args.preset,
        difficulty_id=args.difficulty,
        seed=args.seed,
        load_name=args.load,
    )


if __name__ == "__main__":
    main()
