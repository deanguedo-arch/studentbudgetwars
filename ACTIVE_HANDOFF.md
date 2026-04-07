# Active Handoff

## Current State
- **Branch**: `main`
- **Worktree**: Cleaned up and modernized.
- **Completed**: Phase 1, 2, 3, and 4 engine changes are fully implemented and verified. 
- **Testing**: 54/54 tests passing. (Note: `test_desktop_windowing.py` may fail in headless CI environments because it requires Tkinter display).
- **Saves**: Version bumped to 9. Old saves are correctly invalidated.

## What Changed Most Recently
- **Phase 3 (Chained Events)**: `GameState` now has a `pending_events` queue. Events like "Beater Breakdown" set a ticking time-bomb for "Vehicle Total Loss" 4 months later. Engine force-fires these when the timer hits zero.
- **Phase 4 (Mechanical Constraints)**: 
  - **Energy Cap**: Player income from gig-work and variable tracks is heavily penalized (0.6x) if Energy drops below 30.
  - **Social Lifeline**: If Social Stability > 80, the player's network will automatically bail them out of up to $300 in shortfall once per year, protecting investments from emergency liquidation.
- **UI Warnings**: Outlook panel and Status bar updated to show new dynamic red/green warnings for Energy Caps, Social Isolation, pending consequences, and lifeline availability.

## What the Game Needs to be "Amazing" (Next Steps Roadmap)

The simulation engine is incredibly robust, but the game is still largely a passive spreadsheet. To elevate it to an "amazing" strategy experience, it needs the following three pillars. Here is the surgical guide on how to prompt the next AI (Codex/Claude/etc) to achieve them:

### 1. Interactive Event Choices (The RPG Layer)
**The Gap**: Right now, events just *happen* to the player. They get a log message and stats drop. Amazing narrative games present dilemmas.
**The Fix**: Transform `events.json` so events have 2-3 explicit Choices (e.g., "Car broke down: [Pay $400] | [Ignore it: -40 Reliability] | [Beg Parents: -20 Family Support]").
**How to prompt the AI**: 
> "Refactor the `EventDefinition` model to include a `choices: list[EventChoice]` array instead of flat `immediate_effects`. Each choice should have a label, cost, and stat effects. Update `GameController.resolve_month()` so that if an event fires, the game state pauses and sets a `pending_user_choice_event_id`. Update the Classic UI so `ActionsPanel` gets replaced by choice buttons until the event is resolved."

### 2. High-Impact Visual 'Juice' (The Game Feel Layer)
**The Gap**: Tkinter is static. Hitting a massive sales bonus or suffering a total car loss looks identical in the UI—just numbers changing instantly. 
**The Fix**: Add micro-animations and color flashes to the UI to make positive/negative outcomes viscerally felt.
**How to prompt the AI**:
> "Update `score_strip.py` and `life_panel.py` to use Tkinter's `.after()` loop to smoothly animate the progress bar canvases ticking up/down over 400ms instead of instantly snapping. In `main_window.py`, if the player's `monthly_surplus` drops below zero after a resolve, flash the `FinancePanel`'s background `COLOR_NEGATIVE` fading back to `BG_CARD` over 3 frames."

### 3. Ultimate Win Conditions (The Escape Hatch)
**The Gap**: The game currently ends arbitrarily after 120 months. Players need aspirational targets right from month 1.
**The Fix**: Add ultimate "Win States" (e.g., *Buy a House*, *Start a Business*, *Coast FIRE*) that the player can trigger early if they achieve specific wealth and milestone targets. 
**How to prompt the AI**:
> "Create a `WinStateDefinition` model. Add a new `win_states.json` data file. Update `GameController` to check for eligibility every month. If a player meets the criteria (e.g., $50k net worth and Elite tier), surface a glowing 'Declare Victory: [Goal Name]' button in the `ActionsPanel`. Triggering it ends the run immediately with a massive score multiplier and a specialized endgame screen."

## Quick Technical Reference
- **Classic Entry**: `python3 -m budgetwars.main --mode classic`
- **Tests**: `pytest tests/`
- **Core Loop File**: `src/budgetwars/engine/month_resolution.py`
- **UI Main Window**: `src/budgetwars/games/classic/ui/main_window.py`
