# Active Handoff

## Current State
- Branch: `retro-market-overhaul`
- Status: the repo has been converted from the weekly survival-manager loop into the new daily market-hustle architecture.
- Validation status: `tools/validate_data.py` passes.
- Test status: `16 passed`.

## What Landed In This Pass
- New daily-turn engine:
  - districts
  - commodities
  - gigs
  - backpack capacity
  - board events
  - study / weekly academic checks
  - bank actions
  - weekly housing/interest tick
- New retro desktop shell in Tkinter:
  - menu bar
  - status strip
  - goods panel
  - inventory panel
  - action buttons
  - log pane
- New content schema and JSON pack:
  - `commodities.json`
  - `districts.json`
  - `gigs.json`
  - `services.json`
  - `events.json`
  - `presets.json`
  - `data/balance/*.json`
- Old weekly-loop modules and unused weekly data files were removed.
- Simulation tooling was rewired to the new daily engine.

## Key Runtime Shape
- `1 turn = 1 day`
- `7 days = 1 week`
- `12 weeks = 84 turns`
- The player takes one main action per day:
  - travel
  - buy
  - sell
  - work gig
  - rest
  - study
  - bank action
  - use item

## Current Balance Snapshot
- The new loop is functional and deterministic under seed.
- Early simulation samples show the system is playable but not yet well balanced.
- Small sampled result on `normal + balanced` across all presets:
  - some runs complete the term
  - `scholarship_grinder` currently looks strongest
  - heat pressure and end-of-term survival thresholds are still rough

## Most Important Files
- Engine:
  - `src/budgetwars/engine/game_loop.py`
  - `src/budgetwars/engine/turn_resolution.py`
  - `src/budgetwars/engine/market.py`
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
  - `data/commodities.json`
  - `data/districts.json`
  - `data/gigs.json`
  - `data/events.json`
  - `data/presets.json`

## Known Limits
- Balance is not finished.
- District identity is present but still not sharp enough.
- The Tkinter shell is functional and readable, but still not fully screenshot-close.
- Some policies complete the term but fail survival checks due to net-worth / heat pressure.

## Recommended Next Pass
- Do a focused balance and content-depth pass on the new loop:
  - sharpen district opportunity identity
  - improve commodity spreads and event spikes
  - rebalance heat accumulation
  - tune preset survivability bands
  - deepen gigs/items without bloating actions
