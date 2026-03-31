# Data File Intent

## `config.json`

Global runtime settings such as starting week, term length, seed defaults, and core bounds.
This file also includes difficulty definitions and weekly engine thresholds such as event chance, energy fail windows, debt limits, and autosave naming.
It also defines `job_switch_stress_penalty` for the switch-job tradeoff.

## `items.json`

Item definitions for future inventory or resource systems. Each item should include an id, display name, category, price, and a small effect payload.
Current valid effect keys: `cash`, `savings`, `debt`, `stress`, `energy`.

## `expenses.json`

Recurring or one-off expense definitions with ids, labels, amount, cadence, and whether the expense is mandatory.
In the current prototype, weekly expenses are the main recurring financial pressure.
Optional expenses can include `pay_effects` and `skip_effects` to support decision tradeoffs.
Optional expenses can also include `pay_temporary_effects` and `skip_temporary_effects`.
Each temporary effect entry contains:
- `id`
- `label`
- `duration_weeks`
- `effects`
Design expectation:
- mandatory expenses represent baseline survival costs
- optional expenses represent upkeep/lifestyle choices with real tradeoffs

## `jobs.json`

Job definitions with ids, names, pay ranges, energy cost, stress impact, and eligibility rules.
Jobs currently drive weekly income, energy loss, and stress gain when the player chooses to work.
Jobs can define `work_temporary_effects` that are added after a work week and apply starting the following week.
Balancing intent is distinct job profiles instead of minor numeric variations.

## `locations.json`

Location definitions with ids, names, descriptions, and simple modifiers that may affect jobs, costs, or events.
Location modifiers apply once per week during weekly resolution using the same effect-key set.

## `events.json`

Random event definitions with ids, names, descriptions, probability weight, base effects, and optional structured choices.
Each event should have at least one choice. Choice effects use the same valid effect keys as items.
Events and event choices can also attach `temporary_effects` with the same temporary-effect shape.
This enables short-lived consequences that carry into future weeks.

## `presets.json`

Starting player archetypes containing initial cash, savings, debt, stress, energy, and default location/job references.
Presets should be materially different enough to shape the early-term budget feel.
Each preset should imply a different early-game survival strategy.

## `scoring.json`

Weights and thresholds for end-of-run scoring so the balance can evolve without changing scoring code.

## Effect Key Reference

These keys are currently supported by the game logic and validator:

- `cash`
- `savings`
- `debt`
- `stress`
- `energy`

## Temporary Effect Rules

- Valid only on expense pay/skip temporary fields, job work temporary fields, and event/event-choice temporary fields.
- `duration_weeks` must be positive and currently validated to a small sane range.
- Temporary effects use the same effect key set as direct effects.
