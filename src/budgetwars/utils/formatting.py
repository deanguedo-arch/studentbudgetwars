from __future__ import annotations


def format_currency(value: int) -> str:
    return f"${value:,}"


def format_stat_line(label: str, value: object) -> str:
    return f"{label}: {value}"


def format_signed(value: int | float) -> str:
    prefix = "+" if value >= 0 else ""
    return f"{prefix}{value}"
