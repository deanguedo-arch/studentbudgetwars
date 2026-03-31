# Active Handoff

## Current State
- Branch: `main`
- Status: balance and winnability tuning is implemented in working tree and ready to ship.
- Test status: `62 passed` (full suite).

## What Landed In This Pass
- Economy and survivability were rebalanced in core data:
  - lower mandatory weekly burden
  - lower debt interest / overdraft pressure
  - stronger weekly job income
  - better starting cash/savings/debt buffers
- Simulation policy was tightened so the balanced policy moves to the job location before taking avoidable offsite strain.
- Winnability smoke tests were added so the repo now guards against sliding back into obvious auto-lose balance.

## Current Balance Snapshot
- Mandatory weekly essentials are now materially lower than the earlier unwinnable build.
- Sampled simulation results after tuning:
  - `normal + balanced`: about `50.7%` survival overall
  - `default_student`: about `60%` survival
  - `commuter_student`: about `92%` survival
  - `easy + balanced`: `100%` survival in the sampled runs
- Important caveat:
  - `financially_stretched_student` on `normal` is still too punishing and remains the clearest balance outlier.

## Files Updated
- `src/budgetwars/simulation.py`
- `data/config.json`
- `data/expenses.json`
- `data/jobs.json`
- `data/presets.json`
- `tests/test_balance_profiles.py`
- `tests/test_simulation.py`

## Known Limits (Intentional)
- The game now has winning lanes, but preset spread is still too wide.
- `commuter_student` is currently safer than intended.
- `financially_stretched_student` is still not healthy on `normal`.

## Recommended Next Pass
- Do a focused preset-economy pass:
  - bring `financially_stretched_student` off zero on `normal`
  - pull `commuter_student` back from near-free survival
  - preserve the current “easy is clearly winnable” baseline
