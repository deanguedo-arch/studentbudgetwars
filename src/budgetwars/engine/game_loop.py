from __future__ import annotations

from random import Random

from budgetwars.models import ContentBundle, FinalScoreSummary, GameState

from .budgeting import pay_named_cost
from .effects import append_log, clamp_player_state, trim_logs
from .education import can_switch_education
from .events import eligible_events
from .housing import can_switch_housing
from .lookups import (
    get_budget_stance,
    get_career_track,
    get_city,
    get_current_career_tier,
    get_difficulty,
    get_education_program,
    get_focus_action,
    get_housing_option,
    get_opening_path,
    get_preset,
    get_transport_option,
)
from .month_resolution import resolve_month
from .scoring import calculate_final_score
from .setup import build_new_game_state
from .transport import can_switch_transport
from .careers import can_enter_career


class GameController:
    def __init__(self, bundle: ContentBundle, state: GameState):
        self.bundle = bundle
        self.state = state
        self.rng = Random(state.seed)

    @classmethod
    def new_game(
        cls,
        bundle: ContentBundle,
        player_name: str,
        preset_id: str | None = None,
        difficulty_id: str = "normal",
        seed: int | None = None,
        city_id: str = "hometown",
        opening_path_id: str = "full_time_work",
    ) -> GameController:
        chosen_preset = preset_id or bundle.presets[0].id
        chosen_seed = seed if seed is not None else bundle.config.default_seed
        state = build_new_game_state(bundle, player_name, chosen_preset, difficulty_id, city_id, opening_path_id, chosen_seed)
        return cls(bundle, state)

    def final_score_summary(self) -> FinalScoreSummary:
        return calculate_final_score(self.bundle, self.state)

    def resolve_month(self) -> None:
        resolve_month(self.bundle, self.state, self.rng)

    def available_careers(self) -> list:
        available = []
        for track in self.bundle.careers:
            allowed, _ = can_enter_career(self.bundle, self.state, track.id)
            if allowed:
                available.append(track)
        return available

    def available_education_programs(self) -> list:
        return list(self.bundle.education_programs)

    def available_housing(self) -> list:
        return list(self.bundle.housing_options)

    def available_transport(self) -> list:
        return list(self.bundle.transport_options)

    def available_budget_stances(self) -> list:
        return list(self.bundle.config.budget_stances)

    def available_focus_actions(self) -> list:
        return list(self.bundle.focus_actions)

    def change_career(self, career_id: str) -> None:
        allowed, reason = can_enter_career(self.bundle, self.state, career_id)
        if not allowed:
            raise ValueError(reason)
        self.state.player.career.track_id = career_id
        self.state.player.career.tier_index = 0
        self.state.player.career.months_in_track = 0
        self.state.player.career.promotion_progress = 0
        append_log(self.state, f"Career pivot: {get_career_track(self.bundle, career_id).name}")
        trim_logs(self.bundle, self.state)

    def change_education(self, program_id: str) -> None:
        allowed, reason = can_switch_education(self.bundle, self.state, program_id)
        if not allowed:
            raise ValueError(reason)
        program = get_education_program(self.bundle, program_id)
        self.state.player.education.program_id = program_id
        self.state.player.education.is_active = program_id != "none"
        self.state.player.education.months_completed = 0 if program_id != "none" else self.state.player.education.months_completed
        self.state.player.education.standing = max(40, min(100, 55 + ((self.state.player.academic_strength - 50) // 2)))
        if program_id == "college":
            self.state.player.education.college_gpa = max(
                1.8,
                min(4.0, round(2.2 + ((self.state.player.academic_strength - 50) * 0.03), 2)),
            )
        append_log(self.state, f"Education plan changed: {program.name}")
        trim_logs(self.bundle, self.state)

    def change_housing(self, housing_id: str) -> None:
        allowed, reason = can_switch_housing(self.bundle, self.state, housing_id)
        if not allowed:
            raise ValueError(reason)
        housing = get_housing_option(self.bundle, housing_id)
        if housing.move_in_cost:
            pay_named_cost(self.state, housing.move_in_cost, f"Move to {housing.name}")
        self.state.player.housing_id = housing_id
        self.state.missed_housing_payments = 0
        append_log(self.state, f"Housing changed: {housing.name}")
        trim_logs(self.bundle, self.state)

    def current_transport_switch_discount(self) -> int:
        return sum(modifier.transport_switch_discount for modifier in self.state.active_modifiers)

    def change_transport(self, transport_id: str) -> None:
        allowed, reason = can_switch_transport(self.bundle, self.state, transport_id)
        if not allowed:
            raise ValueError(reason)
        transport = get_transport_option(self.bundle, transport_id)
        upfront = max(0, transport.upfront_cost - self.current_transport_switch_discount())
        if upfront:
            pay_named_cost(self.state, upfront, f"Switch to {transport.name}")
        self.state.player.transport_id = transport_id
        append_log(self.state, f"Transport changed: {transport.name}")
        trim_logs(self.bundle, self.state)

    def change_budget_stance(self, stance_id: str) -> None:
        if stance_id == self.state.player.budget_stance_id:
            raise ValueError("You already use that budget stance.")
        stance = get_budget_stance(self.bundle, stance_id)
        self.state.player.budget_stance_id = stance_id
        append_log(self.state, f"Budget stance set: {stance.name}")
        trim_logs(self.bundle, self.state)

    def change_focus_action(self, focus_action_id: str) -> None:
        if focus_action_id == self.state.player.selected_focus_action_id:
            raise ValueError("That focus is already selected.")
        focus = get_focus_action(self.bundle, focus_action_id)
        self.state.player.selected_focus_action_id = focus_action_id
        append_log(self.state, f"Monthly focus selected: {focus.name}")
        trim_logs(self.bundle, self.state)

    def build_month_outlook(self) -> list[str]:
        player = self.state.player
        city = get_city(self.bundle, self.state.player.current_city_id)
        housing = get_housing_option(self.bundle, player.housing_id)
        transport = get_transport_option(self.bundle, player.transport_id)
        track = get_career_track(self.bundle, player.career.track_id)
        tier = get_current_career_tier(self.bundle, self.state)
        outlook = [
            f"{city.name}: {city.opportunity_text}",
            f"Pressure: {city.pressure_text}",
            f"Current lane: {tier.label} in {track.name}.",
        ]
        if player.debt > self.state.debt_game_over_threshold * 0.45:
            outlook.append("Debt pressure is starting to dominate your monthly choices.")
        if player.stress >= self.state.burnout_stress_threshold - 10:
            outlook.append("Stress is close to burnout territory. A recovery month may be smarter than another push.")
        elif player.stress >= 60:
            outlook.append("Fastest stress relief right now: Recover, calmer housing, and lighter transport.")
        if player.energy <= self.state.burnout_energy_threshold + 10:
            outlook.append("Energy is running low enough to threaten the next few months.")
        if housing.id == "parents" and self.state.player.family_support <= self.state.minimum_parent_fallback_support + 10:
            outlook.append("Staying at home is financially strong, but the family buffer is thinning.")
        if housing.id == "roommates":
            outlook.append("Roommates save money, but they are still adding steady stress pressure.")
        if transport.id in {"beater_car", "financed_car"}:
            outlook.append("Your transport is costing calm every month. Transit or walking would ease strain if you can afford the tradeoff.")
        if transport.access_level < track.minimum_transport_access:
            outlook.append("Transport is limiting your current career ceiling.")
        if player.education.is_active and player.education.program_id == "college" and player.education.college_gpa < 2.7:
            outlook.append("Your GPA is below the office-job cutoff right now.")
        if player.education.is_active and player.education.standing < 55:
            outlook.append("School is slipping and could slow your long-term upside.")
        if player.career.tier_index < len(track.tiers) - 1:
            next_tier = track.tiers[player.career.tier_index + 1]
            if next_tier.required_minimum_gpa is not None and player.education.college_gpa < next_tier.required_minimum_gpa:
                outlook.append(f"{next_tier.label} needs a {next_tier.required_minimum_gpa:.1f} GPA.")
        if self.state.active_modifiers:
            outlook.append("Active pressure: " + ", ".join(modifier.label for modifier in self.state.active_modifiers))
        if not self.state.active_modifiers and not eligible_events(self.bundle, self.state):
            outlook.append("Quiet month. Your own choices will shape most of the pressure.")
        return outlook[:6]

    def is_finished(self) -> bool:
        return self.state.game_over_reason is not None or self.state.current_month > self.state.total_months
