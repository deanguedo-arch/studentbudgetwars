# Student Budget Wars

Student Budget Wars is a terminal-first Python game prototype about surviving a school term while managing cash, savings, debt, stress, energy, bills, and random life events.

The project is structured around small modules and JSON-driven content so future passes can extend systems surgically without turning the game into one large file. Core state, content loading, validation, save/load, UI, and gameplay flow are intentionally separated.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

## Run

```bash
budgetwars
```

Windows quick launcher:

```bash
live_preview.bat
```

You can pass normal CLI flags through the launcher, for example:

```bash
live_preview.bat --preset commuter_student --difficulty hard
```

## Simulation And Balance Audit

Run non-interactive simulations against the real weekly game loop:

```bash
python tools/simulate_runs.py --preset default_student --runs 100 --difficulty normal --policy balanced --seed 42
```

Compare multiple presets in one run:

```bash
python tools/simulate_runs.py --preset default_student,commuter_student,financially_stretched_student --runs 50 --policy cash_hungry --seed 42
```

Optional report artifacts:

```bash
python tools/simulate_runs.py --runs 25 --output-json reports/sim_audit.json --output-csv reports/sim_runs.csv
```

Available simulation policies:
- `balanced`: prefers stability, avoids collapse, and only chases cash when debt pressure is high
- `cash_hungry`: prioritizes income/debt pressure and accepts more stress and energy risk

Reported metrics include runs, survivals, survival rate, average score, average ending resources/stats, common game-over reasons, and breakdowns by preset and starting job.
Use these outputs to tune data values in `data/*.json` and verify whether one preset or strategy is dominating.

Simulation limitations:
- policy decisions are heuristic, not optimal play
- audit outputs show directional balance signals, not perfect balance proofs
- event outcomes remain seeded and deterministic per run seed

## What Exists Now

- Package scaffold for a modular terminal game
- First playable weekly terminal loop with work, rest, buying items, random events, autosave, and end scoring
- Tactical action loop with work/rest resolution plus explicit location moves and job switching
- Compact dashboard-style terminal screen with week outlook and recent-activity window (instead of log dump)
- Typed Pydantic models for config, content, and save state
- JSON loaders and cross-file validation helpers
- Local JSON save/load support
- Rich-based UI for the playable loop
- Minimal but functional game shell and CLI entry point
- Initial pytest coverage for data loading and saves

## What Comes Later

- More weekly actions and decision depth
- Richer budgeting and economy calculations
- Expanded event library and tougher tradeoffs
- More job, location, and item interactions
- Scoring balance and progression tuning
- More content and simulation tooling
