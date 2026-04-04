# After Grad: The First 10 Years

After Grad is now organized as a shared simulation platform with two desktop frontends:

- `Classic`: the current full game experience
- `Desktop`: a separate retro-desktop shell built on the same simulation/session core

The repo still contains one authoritative simulation stack for content, save/load, monthly resolution, scoring, and simulation tooling. Frontends are separate launch paths, not duplicate game engines.

## Run

Canonical launcher:

```bash
budgetwars --mode classic
budgetwars --mode desktop
```

Dedicated entry points:

```bash
budgetwars-classic
budgetwars-desktop
```

Examples:

```bash
budgetwars --mode classic --preset supported_student --city hometown_low_cost --academics strong --family-support high --savings-band solid --path college_university --difficulty easy
budgetwars --mode desktop --load after_grad_autosave.json
```

## Windows Preview

Repo-root preview scripts:

```bat
live_preview.bat
live_preview_classic.bat
live_preview_desktop.bat
```

`live_preview.bat` defaults to Classic mode.

See [PREVIEWING.md](PREVIEWING.md) for usage details.

## macOS Preview

Repo-root double-click launchers:

```bash
open_classic.command
open_desktop.command
```

The Mac launchers bootstrap a local `.venv` and install the runtime deps on first run.

See [PREVIEWING.md](PREVIEWING.md) for usage details and fallback behavior.

## Repo Layout

- `src/budgetwars/models/`: typed content and runtime state
- `src/budgetwars/loaders/`: JSON loading and validation
- `src/budgetwars/engine/`: monthly life-sim rules, scoring, simulation
- `src/budgetwars/saves/`: local JSON save/load
- `src/budgetwars/utils/`: shared helpers
- `src/budgetwars/core/`: mode-aware content/session/bootstrap layer
- `src/budgetwars/games/classic/`: Classic frontend
- `src/budgetwars/games/desktop/`: Desktop frontend
- `data/`: legacy shared content baseline
- `content/`: shared and mode-specific overlay seams

See [ARCHITECTURE.md](ARCHITECTURE.md) for boundary rules and content precedence.

## Content Loading

Mode-aware content resolution uses deterministic file replacement:

1. `content/<mode>/<relative-path>`
2. `content/shared/<relative-path>`
3. `data/<relative-path>`

This keeps the current `data/` payload usable while creating a clean seam for mode-specific overrides.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

## Simulation Tooling

Run deterministic balance batches against the real monthly loop:

```bash
python tools/simulate_runs.py --preset all --difficulty normal --city mid_size_city --academics average --family-support medium --savings-band some --path full_time_work --policy cautious --runs 20 --seed 42
```

Current policies:
- `cautious`
- `ambitious`
