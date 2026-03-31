# Student Budget Wars: City Hustle

Student Budget Wars is now a retro desktop Python game about surviving a school term by moving across campus and the city, spotting temporary price swings, flipping student-life commodities, grinding gigs, keeping your GPA alive, and staying ahead of debt.

The repo keeps the strong parts of the original scaffold:
- JSON-driven content
- typed Pydantic models
- modular engine/UI/save/load layers
- local save files
- deterministic simulation tooling for balance work

The old weekly “life manager” loop has been replaced by a daily market loop.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

## Run

Desktop app:

```bash
budgetwars
```

Windows launcher:

```bash
live_preview.bat
```

Example:

```bash
live_preview.bat --preset dorm_flipper --difficulty hard
```

## Current Game Shape

- `1 turn = 1 day`
- `7 days = 1 week`
- `12 weeks = 84 turns`
- Each day you take one main action:
  - travel
  - buy
  - sell
  - work gig
  - rest
  - study
  - bank action
  - use item
- Each week:
  - housing/utilities/phone hit
  - debt interest hits
  - bank interest applies
  - heat decays
  - academic checkpoint pressure can punish or reward you

Core resources:
- cash
- debt
- bank balance
- energy
- stress
- heat
- GPA
- backpack space
- days left

## Current Content Base

- 10 districts
- 10 tradable commodities
- 9 gigs
- 4 supply/support items
- 12 board and daily events
- 4 starting presets
- 3 difficulties

## Simulation And Balance Audit

Run the non-interactive simulation tool against the real daily loop:

```bash
C:\Users\dean.guedo\AppData\Local\Programs\Python\Python312\python.exe tools\simulate_runs.py --preset dorm_flipper --runs 50 --difficulty normal --policy balanced --seed 42
```

Supported policies:
- `balanced`
- `cash_hungry`

The tool reports:
- run count
- survivals / survival rate
- average score
- average ending cash / bank / debt / stress / energy / GPA
- common game-over reasons
- by-preset balance summary

Optional report outputs:

```bash
tools\simulate_runs.py --preset all --runs 25 --output-json reports\audit.json --output-csv reports\runs.csv
```

## Architecture

- `src/budgetwars/models/`: typed content + runtime state
- `src/budgetwars/loaders/`: JSON loading + validation
- `src/budgetwars/engine/`: market, travel, gigs, study, events, scoring, simulation
- `src/budgetwars/ui/`: retro Tkinter shell
- `src/budgetwars/saves/`: local save manager

## What’s Still Early

- Balance is real but still rough
- The Tkinter shell is functional, not finished-polished
- The commodity board needs more event depth and more district-specific swing
- Gigs and item interactions still have room to deepen

## Best Next Pass

Use simulation output to tighten:
- preset survivability spread
- district opportunity identity
- commodity volatility
- academic pressure vs market pressure
