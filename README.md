# After Grad: The First 10 Years

After Grad is a retro desktop Python life-strategy game about building your position from age 18 to 28.

You start right after graduation, choose a city and opening path, then spend 120 monthly turns juggling:
- work and career progression
- college GPA or training progress
- housing pressure
- transport pressure
- education choices
- debt and savings
- burnout risk
- a small set of concrete life events

The goal is:

**Reach age 28 in the strongest position you can build.**

Money matters, but the game does not score on cash alone. Your ending weighs financial position, career and credentials, housing stability, debt burden, and wellbeing.

## Current V1 Shape

- `1 turn = 1 month`
- `120 turns = 10 years`
- Start flow:
  - choose preset
  - choose city
  - choose opening path
- Persistent systems:
  - career
  - education
  - housing
  - transport
  - budget stance
- Monthly focus actions:
  - `Stack Cash`
  - `Push Forward`
  - `Recover`

## Core V1 Systems

- Housing:
  - parents
  - roommates
  - solo rental
- Transport:
  - walk/bike
  - transit
  - beater car
  - financed car
- Career tracks:
  - service/retail
  - warehouse/logistics
  - trades/apprenticeship
  - office/professional
- Education:
  - none
  - college
  - apprenticeship training

College now tracks a real GPA that can open or block the office/professional lane.
Trades stays on a pass/credential path instead of a GPA path.

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

Example with direct setup values:

```bash
budgetwars --preset supported_student --city hometown --path full_time_work --difficulty easy
```

## Simulation Tooling

Run deterministic balance batches against the real monthly loop:

```bash
C:\Users\dean.guedo\AppData\Local\Programs\Python\Python312\python.exe tools\simulate_runs.py --preset all --difficulty normal --city hometown --path full_time_work --policy conservative --runs 20 --seed 42
```

Current policies:
- `conservative`
- `ambitious`
- `balanced` (alias of `conservative`)

## Architecture

- `src/budgetwars/models/`: typed content and runtime state
- `src/budgetwars/loaders/`: JSON loading and cross-file validation
- `src/budgetwars/engine/`: monthly life-sim rules, scoring, and simulation
- `src/budgetwars/ui/`: retro Tkinter desktop shell
- `src/budgetwars/saves/`: local JSON save/load
- `data/`: all tunable content and balance data

## What Is In Scope Now

- a playable monthly life loop
- graduation setup
- housing and transport pressure
- career and education progression
- concrete failure states
- end-of-run scoring at age 28

## What Is Intentionally Deferred

- partner/shared-relationship systems
- deep social simulation
- school pause/drop/rejoin edge cases
- large city-specific unlock trees
- realism-complete cost breakdowns
- a huge event library
