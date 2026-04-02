# Active Handoff

## Current State
- Baseline branch: `main`
- Latest shipped commit on `main`: `165cc06`
- Validation: `python tools/validate_data.py` passes
- Tests: `python -m pytest -q` passes (`52 passed`)
- Architecture source of truth for this refactor: `docs/surgical-rebuild-roadmap.md`

## What Is Landed
- Two-game architecture is live:
  - shared platform/session layer under `src/budgetwars/core/`
  - `Classic` frontend under `src/budgetwars/games/classic/`
  - `Desktop` frontend under `src/budgetwars/games/desktop/`
- Mode-aware launching is live:
  - `budgetwars --mode classic`
  - `budgetwars --mode desktop`
- Content layering seam is live with deterministic precedence:
  1. base/shared data
  2. mode overlay replacement by file/path
- Root preview launchers are live:
  - `live_preview_classic.bat`
  - `live_preview_desktop.bat`
  - `live_preview.bat` (compat/default flow)

## Desktop Windowing Status
- Desktop app windows are no longer canvas-hosted; they are real `tk.Toplevel` windows with custom XP-style chrome.
- Deterministic activation path is implemented:
  - click on app window content/chrome activates and brings to front
  - taskbar toggle behavior is deterministic (active -> minimize, inactive -> restore/focus)
- Drag/resize updates are direct geometry updates on `Toplevel` windows (no per-move full refresh churn).
- Compact/full action parity for app menus is unified via shared action registries (Mail/Bank/Save flows).
- Tile placement bug (windows being placed outside desktop area) is fixed by using live desktop bounds first.

## Important Files
- Shared core/session:
  - `src/budgetwars/core/startup.py`
  - `src/budgetwars/core/content.py`
  - `src/budgetwars/core/session.py`
- Launching:
  - `src/budgetwars/main.py`
  - `src/budgetwars/launcher.py`
  - `src/budgetwars/games/classic/launcher.py`
  - `src/budgetwars/games/desktop/launcher.py`
- Desktop frontend:
  - `src/budgetwars/games/desktop/app.py`
- Loader/content overlay behavior:
  - `src/budgetwars/loaders/content_loader.py`
  - `content/shared/`
  - `content/classic/`
  - `content/desktop/`
- Tests:
  - `tests/test_mode_architecture.py`
  - `tests/test_desktop_windowing.py`

## Desktop Reliability Acceptance (Implemented)
1. Reopening an already-open app reuses the same window and activates it.
2. Activating a background window updates active state and taskbar state correctly.
3. Compact menu actions match the same action set used by full toolbars (Bank/Mail).
4. Taskbar minimize/restore is deterministic.
5. Tile layout keeps windows inside desktop bounds.

## Known Follow-Up Area
- Main reliability path is in place; remaining work is visual polish and responsive refinement:
  - title-bar/chrome aesthetics and spacing
  - compact breakpoints and content density polish
  - final XP-style visual tuning

## Quick Run Commands
- Classic: `python -m budgetwars.main --mode classic`
- Desktop: `python -m budgetwars.main --mode desktop --name PreviewPlayer`
- Full tests: `python -m pytest -q`
- Data validation: `python tools/validate_data.py`

## Notes
- Local-only folders like `referencezips/` and `tmp/` are not part of shipped code.
- Shared engine/simulation remains single-copy and authoritative.
