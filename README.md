# After Grad: The First 10 Years

After Grad is a retro desktop Python life-strategy game about building your position from age 18 to 28.

You start right after graduation, choose the shape of your starting life, then spend 120 monthly turns juggling:
- work and career progression
- GPA or training progress
- housing pressure
- transport pressure
- education choices
- debt and savings
- burnout risk
- a small set of concrete life events

The goal is:

**Reach age 28 in the strongest life position you can build.**

Money matters heavily, but the game does not score on cash alone. Your ending weighs net worth, monthly surplus, debt load, career tier, education or credentials, housing stability, life satisfaction, and burnout pressure.

## Current V2 Shape

- `1 turn = 1 month`
- `120 turns = 10 years`
- Start flow:
  - choose preset
  - choose city archetype
  - choose academics level
  - choose family support level
  - choose starting savings band
  - choose opening path
  - choose difficulty
- Persistent systems:
  - career
  - education
  - housing
  - transport
  - budget stance
- Monthly focus actions:
  - `Overtime`
  - `Side Gig`
  - `Promotion Hunt`
  - `Study Push`
  - `Recovery Month`
  - `Social Maintenance`
  - `Move Prep`

## Core Systems

- Housing:
  - parents
  - student residence
  - roommates
  - solo rental
- Transport:
  - none
  - transit
  - bike
  - beater car
  - financed car
  - reliable used car
- Career tracks:
  - retail/service
  - warehouse/logistics
  - delivery/gig
  - office/admin
  - trades/apprenticeship
  - healthcare support
  - sales
  - degree-gated professional
- Education:
  - none
  - part-time college
  - full-time university
  - apprenticeship
  - certificate
  - upgrading

College and university lanes track a real GPA that can open or block higher white-collar lanes.
Trades and certificate lanes use pass-state and credentials instead of GPA.

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
budgetwars --preset supported_student --city hometown_low_cost --academics strong --family-support high --savings-band solid --path college_university --difficulty easy
```

## Simulation Tooling

Run deterministic balance batches against the real monthly loop:

```bash
C:\Users\dean.guedo\AppData\Local\Programs\Python\Python312\python.exe tools\simulate_runs.py --preset all --difficulty normal --city mid_size_city --academics average --family-support medium --savings-band some --path full_time_work --policy cautious --runs 20 --seed 42
```

Current policies:
- `cautious`
- `ambitious`

## Architecture

- `src/budgetwars/models/`: typed content and runtime state
- `src/budgetwars/loaders/`: JSON loading and cross-file validation
- `src/budgetwars/engine/`: monthly life-sim rules, scoring, and simulation
- `src/budgetwars/ui/`: retro Tkinter desktop shell
- `src/budgetwars/saves/`: local JSON save/load
- `data/`: all tunable content and balance data

## What Is In Scope Now

- a playable monthly life loop
- broader graduation setup
- housing and transport pressure as first-class systems
- distinct career and education lanes
- contextual monthly events
- annual milestone summaries
- crisis warnings and concrete failure states
- end-of-run scoring at age 28

## What Is Intentionally Deferred

- partner/shared-relationship systems
- deep social simulation
- a full relationship tree
- fine-grained tax and bureaucracy simulation
- save migration from older versions
- huge event libraries or city-specific unlock trees
