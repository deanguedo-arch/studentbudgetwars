# Data File Intent

## `config.json`

Global runtime settings such as starting week, term length, seed defaults, and core bounds.
This file also includes difficulty definitions and weekly engine thresholds such as event chance, energy fail windows, debt limits, and autosave naming.

## `items.json`

Item definitions for future inventory or resource systems. Each item should include an id, display name, category, price, and a small effect payload.
Current valid effect keys: `cash`, `savings`, `debt`, `stress`, `energy`.

## `expenses.json`

Recurring or one-off expense definitions with ids, labels, amount, cadence, and whether the expense is mandatory.
In the current prototype, weekly expenses are the main recurring financial pressure.

## `jobs.json`

Job definitions with ids, names, pay ranges, energy cost, stress impact, and eligibility rules.
Jobs currently drive weekly income, energy loss, and stress gain when the player chooses to work.

## `locations.json`

Location definitions with ids, names, descriptions, and simple modifiers that may affect jobs, costs, or events.
Location modifiers currently validate against the same effect-key set, even though the loop does not fully apply them yet.

## `events.json`

Random event definitions with ids, names, descriptions, probability weight, base effects, and optional structured choices.
Each event should have at least one choice. Choice effects use the same valid effect keys as items.

## `presets.json`

Starting player archetypes containing initial cash, savings, debt, stress, energy, and default location/job references.
Presets should be materially different enough to shape the early-term budget feel.

## `scoring.json`

Weights and thresholds for end-of-run scoring so the balance can evolve without changing scoring code.

## Effect Key Reference

These keys are currently supported by the game logic and validator:

- `cash`
- `savings`
- `debt`
- `stress`
- `energy`
