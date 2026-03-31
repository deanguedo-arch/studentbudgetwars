# Active Handoff

## Current State
- Branch: `main`
- Status: loop redesign + terminal UX cleanup + stability hardening is implemented in working tree and ready to ship.
- Test status: `59 passed` (full suite).

## What Landed In This Pass
- Core loop rhythm tightened around tactical actions:
  - `work`, `rest`, `move location`, `switch job`, `buy item`, `save and quit`
- Location choice made central:
  - new `move_location(...)` helper
  - dedicated move action in game loop
  - config-driven location move friction (`location_move_stress_penalty`)
  - config-driven offsite work penalties when working away from job location
- UI now favors readability over transcript logs:
  - compact dashboard layout (`render_game_screen`)
  - persistent status + position + week outlook + recent activity + action panel
  - activity window capped to recent lines for normal terminal readability
- Weekly message spam reduced:
  - routine accounting lines compressed into weekly summaries
  - key consequences preserved in recent log
- Simulation compatibility preserved and extended:
  - simulation policies now include a location decision hook

## Files Updated
- `src/budgetwars/game.py`
- `src/budgetwars/ui.py`
- `src/budgetwars/locations.py`
- `src/budgetwars/models.py`
- `src/budgetwars/validators.py`
- `src/budgetwars/simulation.py`
- `data/config.json`
- `tests/test_loop_redesign.py` (new)
- `tests/test_temporary_effects.py`
- `tests/test_simulation.py`
- `tests/test_validators.py`
- `README.md`
- `docs/gameplay-loop.md`
- `docs/data-schema.md`
- `docs/product.md`

## Known Limits (Intentional)
- No map/pathfinding/travel graph added.
- No giant market subsystem added yet.
- Week outlook is heuristic and lightweight by design.

## Recommended Next Pass
- Add a lightweight weekly opportunity board (rotating pressure/opportunity signals) that changes tactical value of jobs/locations week-to-week without introducing a large new system.
