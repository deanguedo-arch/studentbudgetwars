"""Run local deterministic simulation batches for balance auditing."""

from __future__ import annotations

import argparse
from pathlib import Path

from budgetwars.loaders import load_all_content
from budgetwars.simulation import (
    POLICIES,
    build_balance_audit,
    format_balance_audit,
    run_simulation_batch,
    write_csv_report,
    write_json_report,
)


def _comma_split(values: list[str] | None) -> list[str]:
    if not values:
        return []
    resolved: list[str] = []
    for value in values:
        resolved.extend(item.strip() for item in value.split(",") if item.strip())
    return resolved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run non-interactive Student Budget Wars simulations.")
    parser.add_argument("--preset", action="append", help="Preset id(s). Comma-separated values are supported.")
    parser.add_argument("--difficulty", default="normal", help="Difficulty id (default: normal).")
    parser.add_argument("--runs", type=int, default=100, help="Runs per preset (default: 100).")
    parser.add_argument(
        "--policy",
        default="balanced",
        choices=sorted(POLICIES.keys()),
        help="Simulation policy to use.",
    )
    parser.add_argument("--seed", type=int, help="Base seed (deterministic if provided).")
    parser.add_argument("--output-json", help="Optional path to write a JSON report.")
    parser.add_argument("--output-csv", help="Optional path to write per-run CSV results.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    bundle = load_all_content()
    selected_presets = _comma_split(args.preset) or [preset.id for preset in bundle.presets]
    known_presets = {preset.id for preset in bundle.presets}
    unknown_presets = sorted(set(selected_presets) - known_presets)
    if unknown_presets:
        parser.error(f"Unknown preset id(s): {', '.join(unknown_presets)}")

    results = run_simulation_batch(
        bundle,
        preset_ids=selected_presets,
        difficulty_id=args.difficulty,
        runs_per_preset=args.runs,
        policy_name=args.policy,
        seed=args.seed,
    )
    audit = build_balance_audit(results)
    print(format_balance_audit(audit))

    if args.output_json:
        json_path = Path(args.output_json)
        write_json_report(json_path, audit=audit, results=results)
        print(f"Wrote JSON report: {json_path}")
    if args.output_csv:
        csv_path = Path(args.output_csv)
        write_csv_report(csv_path, results=results)
        print(f"Wrote CSV report: {csv_path}")


if __name__ == "__main__":
    main()
