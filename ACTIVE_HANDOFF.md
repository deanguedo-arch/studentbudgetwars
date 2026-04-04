# Active Handoff

## Current State
- Branch: `main`
- Worktree: dirty with the Classic score-chase pass plus Mac compatibility fixes
- Goal in progress: make Classic feel like a score-chasing strategy loop and keep both Classic/Desktop launchable on Mac

## What Changed Most Recently
- Classic now has a live score snapshot wired through the shared session/controller layer.
- Classic setup was rebuilt into one integrated dialog instead of the old multi-modal selection chain.
- Classic chrome was simplified so `Resolve Month` reads as the main action.
- Mac launchers were added at the repo root:
  - `open_classic.command`
  - `open_desktop.command`
- Mac launchers now bootstrap `.venv` and install runtime deps on first run.
- Python 3.9 compatibility fixes were applied so the app can import on the local Mac shell.

## Important Files
- Score/runtime seam:
  - `src/budgetwars/engine/scoring.py`
  - `src/budgetwars/engine/game_loop.py`
  - `src/budgetwars/core/session.py`
  - `src/budgetwars/models/state.py`
- Classic UI:
  - `src/budgetwars/games/classic/ui/main_window.py`
  - `src/budgetwars/games/classic/ui/panes/status_bar.py`
  - `src/budgetwars/games/classic/ui/panes/actions_panel.py`
  - `src/budgetwars/games/classic/ui/panes/life_panel.py`
  - `src/budgetwars/games/classic/ui/panes/finance_panel.py`
  - `src/budgetwars/games/classic/ui/panes/log_panel.py`
- Mac launchers and docs:
  - `open_classic.command`
  - `open_desktop.command`
  - `PREVIEWING.md`
  - `README.md`
- Compatibility fixes:
  - `pyproject.toml`
  - `src/budgetwars/core/startup.py`
  - `src/budgetwars/engine/budgeting.py`
  - `src/budgetwars/engine/month_resolution.py`
  - `src/budgetwars/engine/simulation.py`
  - `src/budgetwars/games/desktop/app.py`
  - `src/budgetwars/loaders/__init__.py`

## Verification Status
- Passed: `python3 -m pytest tests/test_mode_architecture.py`
- Failed in this shell: `tests/test_desktop_windowing.py` aborts because Tk needs a GUI display and this terminal session is headless
- Passed: source import probe in a fresh Python 3.9 venv with `pydantic` + `eval-type-backport`

## Next Best Checks
1. Open `open_classic.command` on the Mac and confirm the bootstrap venv gets created on first launch.
2. Open `open_desktop.command` and confirm Desktop comes up with the same bootstrap flow.
3. If you want more polish, continue Classic UI work: setup screen layout, score strip, and month recap tuning.

## Quick Resume
- Classic: `python3 -m budgetwars.main --mode classic`
- Desktop: `python3 -m budgetwars.main --mode desktop --name PreviewPlayer`
- Classic tests: `python3 -m pytest tests/test_mode_architecture.py`

