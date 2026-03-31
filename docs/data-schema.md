# Data File Intent

## `config.json`

Global runtime settings such as starting week, term length, seed defaults, and core bounds.
This file also includes difficulty definitions and weekly engine thresholds such as event chance, energy fail windows, debt limits, and autosave naming.

## `items.json`

Item definitions for future inventory or resource systems. Each item should include an id, display name, category, price, and a small effect payload.

## `expenses.json`

Recurring or one-off expense definitions with ids, labels, amount, cadence, and whether the expense is mandatory.

## `jobs.json`

Job definitions with ids, names, pay ranges, energy cost, stress impact, and eligibility rules.

## `locations.json`

Location definitions with ids, names, descriptions, and simple modifiers that may affect jobs, costs, or events.

## `events.json`

Random event definitions with ids, names, descriptions, probability weight, base effects, and optional structured choices.

## `presets.json`

Starting player archetypes containing initial cash, savings, debt, stress, energy, and default location/job references.

## `scoring.json`

Weights and thresholds for end-of-run scoring so the balance can evolve without changing scoring code.
