# Active Handoff

## Current State
- **Branch**: `main`
- **Latest pushed commit**: `bf1c1e1` (`classic ui: expose consequence signals in pressure and feedback`)
- **Scope**: Classic mode consequence-depth roadmap passes through UI exposure are implemented.
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
- Added explicit consequence exposure in Classic UI:
  - `Pressure family`
  - `Month driver`
  - `Pending fallout` count
  - pending decision signals (situation choice / promotion branch)
- Added causal `Month Driver` line in `Run Feedback`.
- Wired these through `PressureSummaryVM` and `MainWindow` feedback builders.

## Files Touched In Latest Pass
- `src/budgetwars/games/classic/ui/main_window.py`
- `src/budgetwars/games/classic/ui/panes/finance_panel.py`
- `tests/games/classic/test_main_window.py`

## Verification
- Full test suite (venv): `158 passed`
- Command used: `.\.venv\Scripts\python -m pytest -q`

## Known Gaps / Next Work
The checklist phase sequence is complete, but gameplay depth can still be pushed in these targeted follow-ups:
1. **Situation depth v3**: more high-impact branch/build-locked chains, especially mid/late game.
2. **Career breadth**: extend full branch depth beyond retail + warehouse families.
3. **Credit model v3**: tighten growth/decay cadence and make access consequences more consistently felt.
4. **Wealth model v2**: deepen liquidity/drawdown/upside windows and corresponding event hooks.
5. **Balance pass**: stress and credit pacing tuning, especially on easy mode.
6. **Layout polish pass**: fullscreen fit/density cleanup now that consequence signals are surfaced.

## Quick Technical Reference
- **Classic entry**: `python -m budgetwars.main --mode classic`
- **Tests**: `.\.venv\Scripts\python -m pytest -q`
- **Core turn loop**: `src/budgetwars/engine/month_resolution.py`
- **Event selection/scaling**: `src/budgetwars/engine/events.py`
- **Classic UI root**: `src/budgetwars/games/classic/ui/main_window.py`
