# Active Handoff

## Current State
- Branch: `after-grad-life-sim-v2`
- Status: the repo now runs on the expanded monthly after-grad life-sim branch built from current `main`, not from the old market prototype.
- Validation status: `tools/validate_data.py` targets the v2 content bundle.
- Test status: `25 passed`.

## What Landed In This Pass
- Expanded setup flow:
  - preset
  - city archetype
  - academics level
  - family support level
  - starting savings band
  - opening path
  - difficulty
- Broader monthly engine:
  - explicit monthly income, expenses, and surplus
  - nested housing and transport runtime state
  - broader career roster with distinct logic
  - broader education roster with GPA or pass-state gating
  - broader budget stances and focus actions
  - contextual event roster with carryover modifiers
  - annual milestone summaries
  - crisis warning generation
  - expanded ending labels and scoring
- Tkinter shell widened to support the fuller state:
  - setup modals for all startup steps
  - life setup panel
  - month outlook panel
  - finances/progress/pressure panel
  - milestone dialog
  - clearer end-state dialog
- Simulation tooling widened to support the broader setup variables.

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
- Balance is broader, but not finished.
- Setup is now fuller and more expressive, but it needs feel-testing for speed.
- The monthly loop is stronger, but event writing and distinct city personality can still sharpen a lot.
- Social stability is intentionally lightweight and should stay that way unless a future pass can make it genuinely matter.

## Recommended Next Pass
- Do a balance-and-feel pass, not another scope expansion:
  - tighten early-game pressure across presets and opening paths
  - sharpen city identity in the first 12 months
  - improve crisis presentation tone and visibility
  - tune transport trap severity, especially financed car and beater paths
  - use simulation to find clearly dominant or dead-end setups
