"""Run local deterministic simulation batches for Student Budget Wars: City Hustle."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from budgetwars.engine import POLICIES, run_simulation, summarize_runs
from budgetwars.loaders import load_all_content


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run non-interactive Student Budget Wars simulations.")
    parser.add_argument("--preset", default="all", help="Preset id or 'all'.")
    parser.add_argument("--difficulty", default="normal", help="Difficulty id (default: normal).")
    parser.add_argument("--runs", type=int, default=50, help="Runs per preset (default: 50).")
    parser.add_argument("--policy", default="balanced", choices=sorted(POLICIES), help="Policy name.")
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
    preset_ids = [preset.id for preset in bundle.presets] if args.preset == "all" else [args.preset]

    all_results = []
    for index, preset_id in enumerate(preset_ids):
        all_results.extend(
            run_simulation(
                bundle=bundle,
                preset_id=preset_id,
                difficulty_id=args.difficulty,
                runs=args.runs,
                policy_name=args.policy,
                seed=args.seed + (index * 10_000),
            )
        )

    summary = summarize_runs(all_results)
    print(json.dumps(summary, indent=2))

    if args.output_json:
        _write_json(Path(args.output_json), {"summary": summary, "results": [result.__dict__ for result in all_results]})
    if args.output_csv:
        _write_csv(Path(args.output_csv), [result.__dict__ for result in all_results])


if __name__ == "__main__":
    main()
