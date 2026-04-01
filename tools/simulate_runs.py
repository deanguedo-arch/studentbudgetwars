"""Run local deterministic simulation batches for After Grad: The First 10 Years."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from budgetwars.engine import POLICIES, run_simulation, summarize_runs
from budgetwars.engine.simulation import serialize_run_results
from budgetwars.loaders import load_all_content


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run non-interactive After Grad life-sim batches.")
    parser.add_argument("--preset", default="all", help="Preset id or 'all'.")
    parser.add_argument("--difficulty", default="normal", help="Difficulty id (default: normal).")
    parser.add_argument("--city", default="hometown", help="City archetype id (default: hometown).")
    parser.add_argument("--path", dest="opening_path", default="full_time_work", help="Opening path id.")
    parser.add_argument("--runs", type=int, default=25, help="Runs per preset (default: 25).")
    parser.add_argument("--policy", default="conservative", choices=sorted(POLICIES), help="Policy name.")
    parser.add_argument("--seed", type=int, default=42, help="Base deterministic seed.")
    parser.add_argument("--output-json", help="Optional aggregate JSON report path.")
    parser.add_argument("--output-csv", help="Optional per-run CSV report path.")
    return parser


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = build_parser().parse_args()
    bundle = load_all_content()
    results = run_simulation(
        bundle=bundle,
        preset_id=args.preset,
        difficulty_id=args.difficulty,
        city_id=args.city,
        opening_path_id=args.opening_path,
        runs=args.runs,
        policy_name=args.policy,
        seed=args.seed,
    )
    serialized = serialize_run_results(results)
    summary = summarize_runs(results)
    print(json.dumps(summary, indent=2))

    if args.output_json:
        _write_json(Path(args.output_json), {"summary": summary, "results": serialized})
    if args.output_csv:
        _write_csv(Path(args.output_csv), serialized)


if __name__ == "__main__":
    main()
