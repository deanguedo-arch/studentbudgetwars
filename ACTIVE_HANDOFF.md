# Active Handoff

## Current State
- Branch: `after-grad-consequence-depth-pass`
- Status: consequence-depth pass in progress on top of current `main` monthly after-grad runtime.
- Validation status: `tools/validate_data.py` targets the v2 content bundle.
- Test status: pending final pass run after consequence-depth edits.

## What Landed In This Pass
- Career consequence deepening:
  - switch friction costs and transition drag
  - track-specific promotion blockers
  - promotion momentum + performance trend tags
- Housing/transport consequence deepening:
  - housing stability and move-instability penalties
  - transport reliability score and switch friction
- Education re-entry friction:
  - late re-entry cash/stress cost and temporary progress drag
- Financial consequence layer:
  - wealth allocation each month (safe/index/growth/debt)
  - market regimes with monthly return variance
- Contextual pressure events:
  - added family/social/market-shock events tied to path state
- UI visibility upgrades:
  - trajectory lines for momentum, housing stability, transport reliability, and market regime

## Key Runtime Shape
- `1 turn = 1 month`
- `120 turns = 10 years`
- Main persistent systems:
  - career
  - education
  - housing
  - transport
  - budget stance
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
- Investing is broad-bucket based; no manual portfolio micro-control yet.
- Some track identity still relies on rules in code rather than fully data-authored gating tables.

## Recommended Next Pass
- Balance audit pass driven by simulation evidence:
  - verify no single debt-invest strategy dominates
  - tune financed-car and late-school re-entry trap severity
  - calibrate career switch friction so pivots are meaningful but still viable
