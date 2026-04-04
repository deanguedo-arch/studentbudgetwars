from __future__ import annotations

from pathlib import Path

from budgetwars.engine import GameController
from budgetwars.models import ContentBundle, FileSystemPaths, FinalScoreSummary, GameState, LiveScoreSnapshot
from budgetwars.saves import default_paths, load_game, load_named_game, save_game, save_named_game

from .content import load_mode_content
from .startup import GameMode, StartupOptions


class GameSession:
    def __init__(
        self,
        *,
        mode: GameMode,
        options: StartupOptions,
        paths: FileSystemPaths,
        bundle: ContentBundle,
        controller: GameController | None = None,
    ):
        self.mode = mode
        self.options = options
        self.paths = paths
        self.bundle = bundle
        self.controller = controller

    @classmethod
    def from_startup_options(cls, options: StartupOptions, *, root: Path | None = None) -> GameSession:
        paths = default_paths(root)
        bundle = load_mode_content(paths.root, options.mode)
        session = cls(mode=options.mode, options=options, paths=paths, bundle=bundle)
        if options.load_name:
            session.load_named(options.load_name)
        elif options.is_new_game_complete():
            session.start_new_game(options)
        return session

    @classmethod
    def load_from_path(
        cls,
        save_path: Path,
        *,
        mode: GameMode = "classic",
        root: Path | None = None,
    ) -> GameSession:
        options = StartupOptions(mode=mode, load_name=save_path.name)
        paths = default_paths(root)
        bundle = load_mode_content(paths.root, mode)
        state = load_game(save_path)
        controller = GameController(bundle, state)
        return cls(mode=mode, options=options, paths=paths, bundle=bundle, controller=controller)

    @property
    def has_active_game(self) -> bool:
        return self.controller is not None

    @property
    def state(self) -> GameState:
        return self.require_controller().state

    def require_controller(self) -> GameController:
        if self.controller is None:
            raise ValueError("The session has not started a game yet.")
        return self.controller

    def refresh_bundle(self) -> ContentBundle:
        self.bundle = load_mode_content(self.paths.root, self.mode)
        if self.controller is not None:
            self.controller.bundle = self.bundle
        return self.bundle

    def start_new_game(self, options: StartupOptions) -> GameController:
        self.options = options
        self.bundle = load_mode_content(self.paths.root, self.mode)
        self.controller = GameController.new_game(
            self.bundle,
            player_name=options.player_name,
            preset_id=options.preset_id or self.bundle.presets[0].id,
            difficulty_id=options.difficulty_id or self.bundle.difficulties[0].id,
            city_id=options.city_id or self.bundle.cities[0].id,
            academic_level_id=options.academic_level_id or self.bundle.config.academic_levels[0].id,
            family_support_level_id=options.family_support_level_id or self.bundle.config.family_support_levels[0].id,
            savings_band_id=options.savings_band_id or self.bundle.config.savings_bands[0].id,
            opening_path_id=options.opening_path_id or self.bundle.config.opening_paths[0].id,
            seed=options.seed,
        )
        return self.controller

    def ensure_started(self, *, default_player_name: str | None = None) -> GameController:
        if self.controller is None:
            self.start_new_game(self.options.completed_with_defaults(self.bundle, default_player_name=default_player_name))
        return self.require_controller()

    def load_named(self, save_name: str) -> GameController:
        save_path = self.paths.saves_dir / save_name
        if save_path.exists():
            state = load_game(save_path)
        else:
            state = load_named_game(save_name, root=self.paths.root)
        self.controller = GameController(self.bundle, state)
        self.options = StartupOptions(mode=self.mode, player_name=state.player.name, load_name=save_name)
        return self.controller

    def resolve_month(self) -> None:
        self.require_controller().resolve_month()

    def save_named(self, save_name: str) -> Path:
        return save_named_game(self.state, save_name, root=self.paths.root)

    def save_to_path(self, save_path: Path) -> Path:
        return save_game(self.state, save_path)

    def autosave(self) -> Path:
        return self.save_named(self.bundle.config.autosave_name)

    def is_finished(self) -> bool:
        return self.require_controller().is_finished()

    def final_score_summary(self) -> FinalScoreSummary:
        return self.require_controller().final_score_summary()

    def live_score_snapshot(self) -> LiveScoreSnapshot:
        return self.require_controller().live_score_snapshot()
