# Active Handoff

## Current State
- **Branch**: `main`
- **Latest commit**: `b714993` (`Stress tuning: make easy-mode recovery reduce pressure in big-city states`)
- **Remote sync**: pushed to `origin/main`
- **Scope focus**: Classic mode consequence depth + one-screen UI + stress/credit clarity
- **Desktop mode**: intentionally untouched

## Recent Shipped Commits (Newest First)
1. `b714993` Stress tuning for Easy + big-city recovery behavior
2. `631398a` Remove duplicate right-panel score and fix top-rank clipping
3. `3e24a18` Surface persistent career commitments in Build + This Month
4. `aa59ba2` Persist career commitment tags from event choices
5. `32d1d00` Clickable event cards + longer-lived scope effects
6. `5709f6d` Center modal popups over game window
7. `799aa65` Restore prominent top-bar score
8. `bad2318` Move season score summary to top bar, remove score strip
9. `f4a34d7` Move category bars to top, replace bottom controls with clickable cards

## What Is Now Working
- Event choice cards are clickable directly (card/title/body, not only footer buttons).
- Promotion/scope decisions persist beyond one month:
  - Longer duration modifiers
  - Persistent lane tags that survive modifier expiry
  - Follow-up events gated by persistent lane tags
- Persistent lane chips are visible in:
  - Build panel
  - This Month panel
- Right panel no longer duplicates large score/tier (score lives in top bar).
- Top bar rank block no longer clips `score + tier`.
- Easy-mode recovery in high-pressure big-city setups no longer feels stuck/rising by default:
  - pressure trend now eases in recovery contexts where appropriate.

## Key Files Changed In This Window
- `src/budgetwars/games/classic/ui/panes/event_popup.py`
- `src/budgetwars/games/classic/ui/panes/status_bar.py`
- `src/budgetwars/games/classic/ui/panes/finance_panel.py`
- `src/budgetwars/games/classic/ui/panes/life_panel.py`
- `src/budgetwars/games/classic/ui/panes/outlook_panel.py`
- `src/budgetwars/games/classic/ui/main_window.py`
- `src/budgetwars/models/content.py`
- `src/budgetwars/models/state.py`
- `src/budgetwars/loaders/validators.py`
- `src/budgetwars/engine/events.py`
- `src/budgetwars/engine/month_resolution.py`
- `data/events.json`
- `tests/test_event_choices_and_win_states.py`
- `tests/test_month_resolution.py`
- `tests/games/classic/test_main_window.py`

## Verification Status
- `tests/games/classic/test_main_window.py`: passing
- `tests/test_event_choices_and_win_states.py`: passing
- `tests/test_month_resolution.py`: passing
- Full suite (excluding desktop windowing env-dependent tests): `162 passed, 6 deselected`
- Note: desktop-windowing tests are environment-limited here due local Tcl/Tk runtime issue.

## Remaining High-Value Next Steps
1. Expand persistent lane tags to additional careers (office/admin, healthcare, trades) for late-run divergence.
2. Add visible “Committed Lanes” chips to right diagnosis panel (optional, if desired) to unify diagnosis + commitments.
3. Tighten credit growth/decay cadence further so recovery windows feel earned but readable.
4. Add more chained events tied to persistent tags, not only temporary modifiers.
5. Continue easy/hard stress pacing calibration by city + build archetype contrast scenarios.

## Quick Reference
- Run Classic: `python -m budgetwars.main --mode classic`
- Run tests: `.\.venv\Scripts\python -m pytest -q`
- Core turn loop: `src/budgetwars/engine/month_resolution.py`
- Event eligibility/weighting: `src/budgetwars/engine/events.py`
- Classic UI orchestration: `src/budgetwars/games/classic/ui/main_window.py`
