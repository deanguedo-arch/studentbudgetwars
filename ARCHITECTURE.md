# Architecture

## Runtime Layers

- Shared simulation platform:
  - `src/budgetwars/models/`
  - `src/budgetwars/loaders/`
  - `src/budgetwars/engine/`
  - `src/budgetwars/saves/`
  - `src/budgetwars/utils/`
- Frontend-facing orchestration:
  - `src/budgetwars/core/`
- Game frontends:
  - `src/budgetwars/games/classic/`
  - `src/budgetwars/games/desktop/`

## Dependency Rules

- `core` may depend on shared simulation packages.
- `games/classic` may depend on `core`.
- `games/desktop` may depend on `core`.
- `core` must not depend on `games/`.
- `games/classic` and `games/desktop` must not import each other.

## Session Boundary

`budgetwars.core.GameSession` is the frontend-safe runtime boundary.

It owns:
- mode-aware content loading
- startup option resolution
- new game creation
- save loading and writing
- controller ownership
- month advancement

Frontends should not build `GameController` directly once a shared session path exists.

## Content Overlay Rule

Content resolution is deterministic and file-based.

Precedence for each required content file:
1. `content/<mode>/<relative-path>`
2. `content/shared/<relative-path>`
3. legacy `data/<relative-path>`

This is file replacement, not magical deep merging.

## Frontend Notes

Classic:
- preserves the current Tkinter game flow
- owns the migrated legacy UI

Desktop:
- owns a separate Tk shell
- uses the same shared session/core contract
- must not import Classic widgets
