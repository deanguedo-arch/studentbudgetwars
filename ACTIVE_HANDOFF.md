# Active Handoff

## Current State
- Branch: `after-grad-life-sim`
- Status: the repo has been rebuilt from the daily city-hustle prototype into the monthly after-grad life sim.
- Validation status: `tools/validate_data.py` targets the new content bundle.
- Test status: `17 passed`.

## What Landed In This Pass
- New monthly engine:
  - graduation setup
  - 120-month life loop
  - housing / transport / budget pressure
  - career progression
  - light education progression with GPA / pass-state gating
  - concrete monthly events
  - end-of-run Life Position scoring
- New content schema and JSON pack:
  - `cities.json`
  - `careers.json`
  - `education.json`
  - `housing.json`
  - `transport.json`
  - `focus_actions.json`
  - `events.json`
  - `presets.json`
  - `data/balance/*.json`
- Tkinter shell rebuilt around the new monthly state:
  - status strip
  - current setup panel
  - month outlook panel
  - finances/progress panel
  - compact recent log
  - monthly action buttons
- Simulation tooling now runs the real monthly life loop instead of the retired commodity loop.
- Old market-hustle runtime modules and tests were removed.

## Key Runtime Shape
- `1 turn = 1 month`
- `120 turns = 10 years`
- Main persistent systems:
  - career
  - education
  - housing
  - transport
  - budget stance
- Monthly focus action:
  - `Stack Cash`
  - `Push Forward`
  - `Recover`
- College now tracks a real GPA.
- Office/professional entry and higher office tiers can be blocked by low GPA.
- Trades progression stays on the apprenticeship credential/pass lane.

## Most Important Files
- Engine:
  - `src/budgetwars/engine/game_loop.py`
  - `src/budgetwars/engine/month_resolution.py`
  - `src/budgetwars/engine/careers.py`
  - `src/budgetwars/engine/education.py`
  - `src/budgetwars/engine/events.py`
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

## Known Limits
- Balance is early, not finished.
- City identity is currently archetype-level, not deep content-level.
- Education is intentionally lightweight in v1.
- There is no city-move system yet.
- The shell is readable and functional, but still a first playable rather than a finished desktop sim.

## Recommended Next Pass
- Do a focused balance and feel pass on the new monthly loop:
  - tune survivability bands across presets and paths
  - deepen city identity without adding huge scope
  - sharpen housing and transport event pressure
  - improve career-track identity text and event flavor
  - add a small annual-summary presentation pass
