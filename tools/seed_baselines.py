"""Placeholder utility for generating starter balance inputs."""

from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    print(f"Baseline seeding placeholder. Project root: {root}")


if __name__ == "__main__":
    main()
