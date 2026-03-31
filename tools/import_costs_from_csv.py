"""Placeholder utility for importing baseline cost data."""

from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    csv_path = root / "research" / "cost_inputs.csv"
    print(f"Import costs placeholder. Source: {csv_path}")


if __name__ == "__main__":
    main()
