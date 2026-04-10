# Active Handoff

## Current State
- **Branch**: `main`
- **Latest local commit**: `c753a63` (`feat: deepen equipment branch events and add windows bootstrap`)
- **Scope**: Classic consequence roadmap is complete through UI exposure, plus follow-up depth/setup polish from April 10, 2026.
- **Desktop mode**: untouched in this sequence.

## Completed Passes (Shipped)
1. `stateful-situations-v2` (`5eba51e`)
2. `career-branches-v2` (`a9c61c0`)
3. `promotion-choice-nodes-v2` (`2d1e210`)
4. `credit-access-pressure-v2` (`690d5aa`)
5. `wealth-risk-signatures-v1` (`162fdaf`)
6. `recovery-routes-v1` (`27616a0`)
7. `score-and-victory-truth-pass` (`74661ee`)
8. `ui-exposure-pass` (`bf1c1e1`)

## What Changed Most Recently
1. **Environment/bootstrap pass**
   - Added workspace defaults for local interpreter + pytest in `.vscode/settings.json`.
   - Added repo-root `bootstrap_windows.bat` for one-command setup on a fresh non-admin Windows machine.
2. **Situation depth v3 increment (warehouse equipment lane)**
   - Added `equipment_specialist_offer` (stable upside hook).
   - Added `equipment_safety_recall` (strained failure-pressure hook).
   - Added contrast coverage in consequence-depth tests.
3. **Laptop-height layout fix (Classic)**
   - Improved root window sizing against working area and lowered minimum window floor.
   - Reduced setup dialog minimum height so bottom controls remain visible on shorter screens.

## Files Touched In Latest Pass
- `.vscode/settings.json`
- `bootstrap_windows.bat`
- `README.md`
- `data/events.json`
- `tests/test_consequence_depth.py`
- `tests/test_content_loading.py`
- `src/budgetwars/games/classic/ui/tk_app.py`
- `src/budgetwars/games/classic/ui/main_window.py`

## Verification
- Full test suite (venv): `159 passed`
- Commands used:
  - `.\.venv\Scripts\python -m pytest -q`
  - `.\.venv\Scripts\python -m pytest tests\games\classic\test_main_window.py -q`
  - `cmd /c bootstrap_windows.bat`

## Known Gaps / Next Work
The checklist phase sequence is complete. Remaining high-value follow-ups:
1. **Situation depth v3**: more high-impact branch/build-locked chains, especially mid/late game.
2. **Career breadth**: extend full branch depth beyond retail + warehouse families (office/admin, healthcare, trades).
3. **Credit model v3**: tighten growth/decay cadence and make access consequences more consistently felt.
4. **Wealth model v2**: deepen liquidity/drawdown/upside windows and corresponding event hooks.
5. **Balance pass**: stress and credit pacing tuning, especially on easy mode and low-height screens.
6. **Classic layout polish pass**: optional manual compact-layout toggle for users who want forced dense mode.

## Quick Technical Reference
- **Classic entry**: `python -m budgetwars.main --mode classic`
- **Tests**: `.\.venv\Scripts\python -m pytest -q`
- **Core turn loop**: `src/budgetwars/engine/month_resolution.py`
- **Event selection/scaling**: `src/budgetwars/engine/events.py`
- **Classic UI root**: `src/budgetwars/games/classic/ui/main_window.py`
