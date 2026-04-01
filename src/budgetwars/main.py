from __future__ import annotations

import argparse

from .app import run_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="After Grad: The First 10 Years")
    parser.add_argument("--load", help="Load a save file from the saves directory.")
    parser.add_argument("--name", default="Player", help="Player name for a new game.")
    parser.add_argument("--preset", help="Preset id for a new game.")
    parser.add_argument("--difficulty", help="Difficulty id for a new game.")
    parser.add_argument("--city", help="City archetype id for a new game.")
    parser.add_argument("--academics", help="Academic level id for a new game.")
    parser.add_argument("--family-support", dest="family_support", help="Family support level id for a new game.")
    parser.add_argument("--savings-band", dest="savings_band", help="Starting savings band id for a new game.")
    parser.add_argument("--path", dest="opening_path", help="Opening path id for a new game.")
    parser.add_argument("--seed", type=int, help="Optional deterministic seed.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_app(
        player_name=args.name,
        preset_id=args.preset,
        difficulty_id=args.difficulty,
        city_id=args.city,
        academic_level_id=args.academics,
        family_support_level_id=args.family_support,
        savings_band_id=args.savings_band,
        opening_path_id=args.opening_path,
        seed=args.seed,
        load_name=args.load,
    )


if __name__ == "__main__":
    main()
