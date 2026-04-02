Yes. Here’s the **exact Codex context + execution prompt**.

This is built against your actual repo shape, not fantasy. Right now you have:

* a single CLI entry at `src/budgetwars/main.py` that calls `run_app(...)` 
* a single app launcher in `src/budgetwars/app.py` that loads content, builds a `GameController`, and launches `BudgetWarsTkApp` 
* a `live_preview.bat` that launches one preview path with `python -m budgetwars.main` 
* a repo architecture already intended around `models`, `loaders`, `engine`, `ui`, `saves`, and `data` 

That means the right move is **not** “make one giant app with flags jammed everywhere.”
The right move is:

* keep one repo
* create one shared core
* split into **two game frontends**
* add **two live previews**
* keep current game alive as **Classic**
* add second game as **Desktop**

---

# 1) CODEx CONTEXT BLOCK

Paste this first as project context/instructions for Codex:

```text
You are working inside the GitHub repo `deanguedo-arch/studentbudgetwars`.

This repo is a Python desktop game project, not a web app.

Ground truth from the repo:

- `pyproject.toml` defines the package `student-budget-wars` and currently exposes one script:
  - `budgetwars = "budgetwars.main:main"`
- `src/budgetwars/main.py` currently parses CLI args like `--load`, `--name`, `--preset`, `--difficulty`, `--city`, `--academics`, `--family-support`, `--savings-band`, `--path`, and `--seed`, then calls `run_app(...)`.
- `src/budgetwars/app.py` currently loads content, builds/loads a `GameController`, and launches `BudgetWarsTkApp`.
- `live_preview.bat` currently launches one preview path via `python -m budgetwars.main --name PreviewPlayer %*`.
- The README describes the architecture as:
  - `src/budgetwars/models/`
  - `src/budgetwars/loaders/`
  - `src/budgetwars/engine/`
  - `src/budgetwars/ui/`
  - `src/budgetwars/saves/`
  - `data/`
- The README also makes clear this is already a real sim with a monthly loop, career, education, housing, transport, debt/savings, wealth strategy, event systems, scoring, and a retro Tkinter desktop shell.

The target is to support TWO SHIPPABLE GAMES from the SAME REPO:

1. `Classic`
   - the current direction
   - strategic/dashboard-oriented
   - preserves the existing experience and momentum

2. `Desktop`
   - a more immersive retro-desktop / Money-Simulator-like direction
   - separate windowed experience
   - stronger diegetic navigation and presentation

Critical architecture rule:
- This is NOT one game with two skins.
- This is one SHARED SIMULATION CORE with TWO SEPARATE GAME FRONTENDS.

So the repo must be refactored into:
- shared core/platform code
- game-specific frontends
- shared + mode-specific content
- separate launchers / live previews

Non-negotiable constraints:
- Do not destroy the current game.
- Do not mix Tkinter UI logic into core simulation logic.
- Do not hardwire desktop-specific assumptions into shared engine code.
- Do not duplicate the engine into two parallel copies.
- Do not perform a giant rewrite that leaves the repo in a broken state.
- Work incrementally and keep the project runnable after each phase.
- Prefer surgical file moves and compatibility shims over reckless rewrites.
- Preserve existing CLI/new-game/load-game behavior where reasonable.
- Add tests where needed for refactored shared logic.
- Keep Windows usability in mind since live preview batch files already exist.

Primary goal:
Refactor this repo into a clean multi-game architecture so I can push and preview BOTH versions from the same repo with minimal duplication and clear boundaries.
```

---

# 2) THE MAIN CODEX EXECUTION PROMPT

Now give Codex this:

```text
Refactor this repository into a TWO-GAME architecture with a SHARED CORE and TWO distinct desktop frontends:

- Game 1: `Classic`
- Game 2: `Desktop`

I want a phase-by-phase implementation carried out directly in the repo.

You must do this SURGICALLY.

## HIGH-LEVEL GOAL

Transform the current project from a single-app structure into:

- one shared simulation core/platform
- one `classic` game frontend
- one `desktop` game frontend
- shared + mode-specific content organization
- separate launchers and separate live preview scripts for both versions
- a root launcher option that can choose mode cleanly

The repo should remain coherent, readable, and maintainable for future agent work in Cursor/Codex.

---

## WHAT TO BUILD

### 1. Shared platform/core boundary

Create a clear shared core layer that contains things like:

- data models
- loading / validation
- engine / turn resolution
- scoring
- saves
- services / orchestration
- shared utilities

Do NOT leave this mixed with game-specific UI code.

The core must be UI-agnostic.

If needed, introduce an orchestrator/session layer that becomes the stable interface between frontends and the engine, such as:

- `GameSession`
- `ActionResult`
- `MonthlySummary`
- `AvailableActions`
- mode-aware content loading

This contract should let both frontends call the same shared simulation platform.

---

### 2. Split the frontends into two game apps

Create:

- `src/budgetwars/games/classic/...`
- `src/budgetwars/games/desktop/...`

Classic:
- preserve the current game direction
- preserve current behavior as much as practical
- migrate existing UI pieces into this area
- keep it strategic and readable

Desktop:
- prepare a separate game shell oriented around a retro desktop/window metaphor
- create the architectural structure even if the UI starts as a minimal shell
- do NOT fake this by just cloning Classic and renaming it
- create real separate app/controller/ui boundaries

The frontends should share the core, not each other’s UI internals.

---

### 3. Restructure content into shared + mode-specific

Create a content organization that supports overrides or extensions, for example:

- `content/shared/...`
- `content/classic/...`
- `content/desktop/...`

or equivalent under the project’s preferred structure.

The loader system should support:
1. shared content
2. mode-specific overlay/override content

Do not overcomplicate this if current loading is still simple, but create the correct long-term seam now.

---

### 4. New launch model

Replace the single-app launch path with a cleaner multi-mode setup.

I want:

- a root launcher that can accept `--mode classic` or `--mode desktop`
- plus dedicated entry points if practical

Examples of acceptable end states:
- `budgetwars --mode classic`
- `budgetwars --mode desktop`

and/or
- `budgetwars-classic`
- `budgetwars-desktop`

The implementation should preserve the existing new-game/load-game argument flow as much as possible.

---

### 5. Bake in TWO LIVE PREVIEWS

This is non-negotiable.

I want BOTH versions to have live preview scripts at the repo root.

Create:
- `live_preview_classic.bat`
- `live_preview_desktop.bat`

Optional but recommended:
- keep a root `live_preview.bat` that defaults to classic or offers a simple mode route

Requirements for each live preview:
- follow the spirit of the current Windows launcher
- locate `.venv\Scripts\python.exe` first
- fall back to local installed Python under `%LocalAppData%\Programs\Python\Python*`
- fall back to `python`
- fail clearly if Python is unavailable
- launch the correct game mode
- pass through extra CLI args
- use a preview player name
- keep the scripts simple and readable

Also create a short `PREVIEWING.md` or add a clear section to the README explaining how to launch:
- Classic preview
- Desktop preview
- mode-based CLI preview

---

### 6. Keep the repo agent-friendly

This repo will be worked on with Cursor/Codex repeatedly.

So optimize for:
- clean folder boundaries
- low ambiguity
- obvious entry points
- minimal giant files
- minimal cross-layer leakage
- good naming
- clear comments only where needed
- future agent navigability

Add/update architecture docs if useful.

---

## REQUIRED TARGET STRUCTURE

Move toward a structure like this, adapted to the repo’s real needs:

- `src/budgetwars/core/...`
- `src/budgetwars/games/classic/...`
- `src/budgetwars/games/desktop/...`
- `src/budgetwars/content/...` or compatible data/content structure
- `tests/core/...`
- `tests/classic/...`
- `tests/desktop/...`

You do NOT need to match this literally if a slightly different structure is cleaner for the existing repo, but the same separation of concerns must exist.

---

## IMPLEMENTATION STRATEGY

Work in phases and keep the repo runnable.

### Phase 1 — establish architecture seams
- identify current single-app entry path
- introduce shared core/session boundary
- create game-mode-aware launcher path
- do not break current behavior

### Phase 2 — migrate current game into Classic
- move/refactor current UI/app wiring into `games/classic`
- keep compatibility shims if needed
- keep this launchable

### Phase 3 — scaffold Desktop
- create `games/desktop`
- create a minimal but real separate app path
- hook it to the same shared core/session boundary
- do not leave it as dead empty folders; it must launch

### Phase 4 — content layering
- introduce shared + mode-specific content seams
- keep backward compatibility where practical

### Phase 5 — launchers and docs
- add the `.bat` live preview scripts
- update CLI entry points
- document exactly how to run both versions

### Phase 6 — cleanup
- remove obsolete imports/paths where safe
- leave shims only if they reduce breakage and confusion
- update tests and docs

---

## OUTPUT REQUIREMENTS

Do the actual refactor in code.

Also create/update:

1. `README.md`
   - explain the two-game architecture
   - explain launch methods
   - explain live previews
   - explain the repo layout at a high level

2. `PREVIEWING.md` or equivalent
   - short practical preview instructions

3. architecture notes file, such as:
   - `ARCHITECTURE.md`
   - explain core vs classic vs desktop boundaries
   - explain what code belongs where
   - explain how future agent work should stay surgical

---

## IMPORTANT BEHAVIOR RULES

- Preserve current game behavior where possible while moving it into Classic.
- Do not build a fake abstraction that immediately leaks.
- Do not duplicate large chunks of engine code unless absolutely unavoidable.
- Prefer adapters, wrappers, and service boundaries to risky deep rewrites.
- Keep imports tidy.
- Keep the code runnable at the end.
- If a perfect refactor is too risky, choose the safest clean intermediate structure and document remaining follow-up steps.

---

## LIVE PREVIEW REQUIREMENTS IN DETAIL

Model the new preview scripts on the existing `live_preview.bat` behavior.

Create at minimum:

### `live_preview_classic.bat`
- launches Classic preview
- uses preview defaults
- forwards extra args

### `live_preview_desktop.bat`
- launches Desktop preview
- uses preview defaults
- forwards extra args

Optional:
### `live_preview.bat`
- default to Classic
- or accept a first argument for mode if that is clean and reliable

Examples of acceptable behavior:
- `live_preview_classic.bat`
- `live_preview_desktop.bat`
- `live_preview_desktop.bat --seed 42`
- `budgetwars --mode desktop --name PreviewPlayer`

---

## WHAT I CARE ABOUT MOST

1. Clear shared-core / two-frontend boundaries
2. Repo structure that works well with Codex/Cursor
3. Minimal duplication
4. Both versions launchable
5. Both live previews baked in
6. Good docs
7. Current game preserved as Classic

Start now and implement this refactor surgically.
```

---

# 3) THE FOLLOW-UP “QUALITY CONTROL” PROMPT

After Codex does the first pass, use this to stop it from lying to you:

```text
Audit your own refactor against these criteria and then fix problems you find:

1. Is the shared core truly UI-agnostic?
2. Did any Classic-specific logic leak into shared core?
3. Did any Desktop-specific logic leak into shared core?
4. Is the current game genuinely preserved as Classic?
5. Is Desktop a real separate launch path, not just a rename?
6. Do both live preview batch files exist and work according to the required fallback logic?
7. Does the root launcher support clean mode selection?
8. Are docs updated and accurate?
9. Are there any obsolete imports or broken compatibility paths?
10. Is the repo easier for future Codex agent work, or did you just reshuffle files?

Then:
- fix structural issues
- tighten docs
- remove obvious dead code
- make final import/path cleanup passes
- leave a concise summary of what changed, what remains intentionally deferred, and what the next best step is
```

---

# 4) THE LIVE PREVIEW-SPECIFIC PROMPT

If you want Codex to focus hard on the preview system after the main refactor, use this:

```text
Implement and verify the live preview system for both game versions.

I need:

- `live_preview_classic.bat`
- `live_preview_desktop.bat`

Behavior requirements:
- `cd /d "%~dp0"`
- prefer `.venv\Scripts\python.exe`
- then check `%LocalAppData%\Programs\Python\Python*`
- then fall back to `python`
- fail clearly if no Python is found
- launch the correct mode
- pass through extra arguments
- use a preview player name
- keep scripts consistent with the repo’s current Windows launcher style

Also decide whether to:
- keep `live_preview.bat` as a default-to-classic wrapper
or
- update it into a simple mode router

Whichever option you choose, make it obvious and documented.

Then update docs so a user can immediately preview:
- Classic
- Desktop
- mode-based CLI launch

Finally do a consistency pass:
- make sure launcher names, CLI mode names, README docs, and batch files all match exactly
- no naming drift
- no fake docs
```

---

# 5) What Codex should probably produce

This is what a good result should roughly end up with:

### New launch paths

* `budgetwars --mode classic`
* `budgetwars --mode desktop`

Possibly also:

* `budgetwars-classic`
* `budgetwars-desktop`

### New root batch files

* `live_preview_classic.bat`
* `live_preview_desktop.bat`

### Likely code split

* `src/budgetwars/core/...`
* `src/budgetwars/games/classic/...`
* `src/budgetwars/games/desktop/...`

### Docs

* updated `README.md`
* `ARCHITECTURE.md`
* `PREVIEWING.md`

---

# 6) The blunt warning you need

Your main risk is not that Codex “can’t do it.”

Your main risk is that Codex will try to be clever and do one of these dumb things:

* create two folders but keep one real app
* leave engine and UI tangled
* rename current UI to Classic and call it architecture
* scaffold Desktop as empty theater
* add mode flags without a real boundary
* write docs that describe a cleaner system than the code actually implements

That’s why you need the **audit prompt** after the main pass.

---

# 7) The shortest usable version

If you want the stripped version to paste fast, use this:

```text
Refactor this repo into a shared-core, two-game architecture.

Games:
- Classic = preserve current direction
- Desktop = separate retro desktop style direction

Requirements:
- one shared simulation core
- separate frontend/app paths for Classic and Desktop
- no UI logic in shared core
- minimal duplication
- current game preserved as Classic
- Desktop launches as a real separate mode
- support `budgetwars --mode classic` and `budgetwars --mode desktop`
- add `live_preview_classic.bat` and `live_preview_desktop.bat`
- both batch files must use the same Python fallback logic as the current `live_preview.bat`
- update README and add architecture/preview docs
- keep the repo runnable after each phase
- prefer surgical refactor with compatibility shims over risky rewrite

Ground truth:
- current single CLI is in `src/budgetwars/main.py`
- current app launcher is in `src/budgetwars/app.py`
- current preview launcher is `live_preview.bat`
- architecture currently centers around engine/loaders/models/ui/saves/data

Do the refactor in phases, keep it runnable, and then audit/fix your own work for leakage, duplication, fake abstractions, broken launchers, and inaccurate docs.
```

If you want, I can also turn this into a **Cursor rules file + Codex task breakdown** so the agent works in smaller controlled passes instead of one giant swing.
