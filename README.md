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

## What Exists Now

- Package scaffold for a modular terminal game
- First playable weekly terminal loop with work, rest, buying items, random events, autosave, and end scoring
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
