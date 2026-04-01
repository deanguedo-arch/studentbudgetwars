# Active Handoff

## Current State
- Branch: `after-grad-texture-visibility-pass`
- Status: texture-and-visibility pass in progress on top of current `main` monthly after-grad runtime.
- Validation status: `tools/validate_data.py` targets the v2 content bundle.
- Test status: `39 passed`.

## What Landed In This Pass
- Explicit wealth strategy layer:
  - separate `wealth_strategy` choice independent of budget stance
  - four strategy profiles with different liquidity/risk/debt priorities
- Housing/transport consequence texture:
  - chained roommate and vehicle events that can echo beyond one month
  - financed-car and stay-at-home paths now surface more concrete pressure
- Stronger path feel:
  - sales hot/cold streak events
  - parent support/boundary events
  - follow-up event gating through active modifier ids
- Visibility upgrades:
  - `Why This Month Changed` driver summary
  - wealth strategy shown in UI alongside budget stance
  - clearer month-to-month causal readout in the center panel

## Key Runtime Shape
- `1 turn = 1 month`
- `120 turns = 10 years`
- Main persistent systems:
  - career
  - education
  - housing
  - transport
  - budget stance
  - wealth strategy
- Monthly focus actions:
  - `overtime`
  - `side_gig`
  - `promotion_hunt`
  - `study_push`
  - `recovery_month`
  - `social_maintenance`
  - `move_prep`
- GPA gates stronger college/professional lanes.
- Trades and certificates use pass-state and credentials instead of GPA.

## Most Important Files
- Engine:
  - `src/budgetwars/engine/game_loop.py`
  - `src/budgetwars/engine/month_resolution.py`
  - `src/budgetwars/engine/careers.py`
  - `src/budgetwars/engine/education.py`
  - `src/budgetwars/engine/events.py`
  - `src/budgetwars/engine/scoring.py`
  - `src/budgetwars/engine/simulation.py`
- UI:
  - `src/budgetwars/ui/main_window.py`
  - `src/budgetwars/ui/tk_app.py`
- Models/loaders:
  - `src/budgetwars/models/`
  - `src/budgetwars/loaders/`
- Data:
  - `data/config.json`
  - `data/cities.json`
  - `data/careers.json`
  - `data/education.json`
  - `data/housing.json`
  - `data/transport.json`
  - `data/focus_actions.json`
  - `data/events.json`
  - `data/presets.json`
  - `data/balance/*.json`

## Known Limits
- Social context is still lightweight and event-driven (by design), not a deep relationship sim.
- Wealth strategy is now explicit, but still profile-based rather than fully custom-rule authored.
- Some track identity still relies on rules in code rather than fully data-authored gating tables.

## Recommended Next Pass
- Balance audit pass driven by simulation evidence:
  - verify no single wealth strategy dominates
  - tune chained event frequency so housing/transport paths feel vivid but not spammy
  - refine month-driver wording so consequences feel sharper and more human
