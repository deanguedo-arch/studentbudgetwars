from __future__ import annotations

from pathlib import Path

from budgetwars.core import StartupOptions
from budgetwars.games.classic.launcher import run_classic
from budgetwars.games.desktop.launcher import run_desktop


def launch_mode(options: StartupOptions, *, root: Path | None = None) -> None:
    normalized = options.with_mode(options.mode)
    if normalized.mode == "desktop":
        run_desktop(normalized, root=root)
        return
    run_classic(normalized, root=root)
