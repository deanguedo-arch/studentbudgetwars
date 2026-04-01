from __future__ import annotations

from random import Random

from budgetwars.models import ContentBundle, FinalScoreSummary, GameState

from .budgeting import pay_named_cost
from .careers import can_enter_career, promotion_blockers
from .education import can_switch_education
from .effects import append_log, trim_logs
from .events import eligible_events
from .housing import can_switch_housing
from .lookups import (
    get_budget_stance,
    get_career_track,
    get_city,
    get_current_career_tier,
    get_education_program,
    get_focus_action,
    get_housing_option,
    get_transport_option,
    get_wealth_strategy,
)
from .month_resolution import resolve_month
from .scoring import calculate_final_score
from .setup import build_new_game_state
from .transport import can_switch_transport


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
        city_id: str = "hometown_low_cost",
        opening_path_id: str = "full_time_work",
        academic_level_id: str = "average",
        family_support_level_id: str = "medium",
        savings_band_id: str = "some",
    ) -> GameController:
        chosen_preset = preset_id or bundle.presets[0].id
        chosen_seed = seed if seed is not None else bundle.config.default_seed
        state = build_new_game_state(
            bundle,
            player_name,
            chosen_preset,
            difficulty_id,
            city_id,
            opening_path_id,
            academic_level_id,
            family_support_level_id,
            savings_band_id,
            chosen_seed,
        )
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

    def career_entry_statuses(self) -> list[tuple[str, str, bool, str]]:
        statuses: list[tuple[str, str, bool, str]] = []
        for track in self.bundle.careers:
            allowed, reason = can_enter_career(self.bundle, self.state, track.id)
            statuses.append((track.name, track.id, allowed, reason))
        return statuses

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

    def available_wealth_strategies(self) -> list:
        return list(self.bundle.wealth_strategies)

    def change_career(self, career_id: str) -> None:
        allowed, reason = can_enter_career(self.bundle, self.state, career_id)
        if not allowed:
            raise ValueError(reason)
        previous_track = self.state.player.career.track_id
        previous_progress = self.state.player.career.promotion_progress
        switch_cost = self.bundle.config.career_switch_cash_cost
        if switch_cost:
            pay_named_cost(self.state, switch_cost, "Career transition cost")
        self.state.player.stress += self.bundle.config.career_switch_stress_cost
        self.state.player.career.track_id = career_id
        self.state.player.career.tier_index = 0
        self.state.player.career.months_in_track = 0
        retained_progress = int(round(previous_progress * (1.0 - self.bundle.config.career_switch_progress_loss_ratio)))
        self.state.player.career.promotion_progress = max(0, retained_progress)
        self.state.player.career.transition_penalty_months = self.bundle.config.career_switch_transition_months
        self.state.player.career.promotion_momentum = max(20, self.state.player.career.promotion_momentum - 12)
        self.state.player.social_stability = max(0, self.state.player.social_stability - 2)
        self.state.player.career.layoff_pressure = 0
        append_log(
            self.state,
            f"Career pivot: {get_career_track(self.bundle, previous_track).name} -> {get_career_track(self.bundle, career_id).name}",
        )
        trim_logs(self.bundle, self.state)

    def change_education(self, program_id: str) -> None:
        allowed, reason = can_switch_education(self.bundle, self.state, program_id)
        if not allowed:
            raise ValueError(reason)
        program = get_education_program(self.bundle, program_id)
        education = self.state.player.education
        if program_id == education.program_id:
            education.is_active = not education.is_active if program.can_pause else education.is_active
            education.is_paused = not education.is_active
            append_log(self.state, f"Education {'resumed' if education.is_active else 'paused'}: {program.name}")
            trim_logs(self.bundle, self.state)
            return
        if education.program_id != "none" and education.months_completed > 0 and education.is_active:
            education.months_completed = int(round(education.months_completed * 0.65))
            self.state.player.stress += 2
            self.state.player.life_satisfaction -= 2
            append_log(self.state, "Switching programs cost progress and added pressure.")
        if program_id != "none" and self.state.current_month > 24:
            if self.bundle.config.education_reentry_cash_cost:
                pay_named_cost(self.state, self.bundle.config.education_reentry_cash_cost, "Education re-entry cost")
            self.state.player.stress += self.bundle.config.education_reentry_stress_cost
            education.reentry_drag_months = max(education.reentry_drag_months, self.bundle.config.education_reentry_drag_months)
            append_log(self.state, "Late school re-entry is possible, but the transition friction is real.")
        education.program_id = program_id
        education.is_active = program_id != "none"
        education.is_paused = False
        education.months_completed = 0 if program_id != "none" else education.months_completed
        education.failure_streak = 0
        education.standing = max(40, min(100, 55 + ((self.state.player.academic_strength - 50) // 2)))
        if program.uses_gpa:
            education.college_gpa = max(1.8, min(4.0, round(2.2 + ((self.state.player.academic_strength - 50) * 0.03), 2)))
        append_log(self.state, f"Education plan changed: {program.name}")
        trim_logs(self.bundle, self.state)

    def current_housing_move_discount(self) -> int:
        discount = 0
        if self.state.player.selected_focus_action_id == "move_prep":
            discount += 160
        return discount

    def change_housing(self, housing_id: str) -> None:
        allowed, reason = can_switch_housing(self.bundle, self.state, housing_id)
        if not allowed:
            raise ValueError(reason)
        housing = get_housing_option(self.bundle, housing_id)
        move_cost = max(0, housing.move_in_cost - self.current_housing_move_discount())
        if move_cost:
            pay_named_cost(self.state, move_cost, f"Move to {housing.name}")
        self.state.player.stress += self.bundle.config.housing_move_stress_penalty
        self.state.player.housing.recent_move_penalty_months = self.bundle.config.housing_move_instability_months
        self.state.player.housing.housing_stability = max(25, self.state.player.housing.housing_stability - 10)
        self.state.player.housing.option_id = housing_id
        self.state.player.housing.months_in_place = 0
        self.state.player.housing.missed_payment_streak = 0
        append_log(self.state, f"Housing changed: {housing.name}")
        trim_logs(self.bundle, self.state)

    def current_transport_switch_discount(self) -> int:
        discount = sum(modifier.transport_switch_discount for modifier in self.state.active_modifiers)
        if self.state.player.selected_focus_action_id == "move_prep":
            discount += 120
        return discount

    def change_transport(self, transport_id: str) -> None:
        allowed, reason = can_switch_transport(self.bundle, self.state, transport_id)
        if not allowed:
            raise ValueError(reason)
        transport = get_transport_option(self.bundle, transport_id)
        upfront = max(0, transport.upfront_cost - self.current_transport_switch_discount())
        if upfront:
            pay_named_cost(self.state, upfront, f"Switch to {transport.name}")
        if self.bundle.config.transport_switch_admin_cost:
            pay_named_cost(self.state, self.bundle.config.transport_switch_admin_cost, "Transport switch admin")
        if self.state.player.transport.option_id == "financed_car" and transport_id != "financed_car":
            pay_named_cost(self.state, 280, "Vehicle disposition loss")
        self.state.player.stress += self.bundle.config.transport_switch_stress_penalty
        self.state.player.transport.recent_switch_penalty_months = self.bundle.config.transport_switch_instability_months
        self.state.player.transport.reliability_score = max(35, self.state.player.transport.reliability_score - 8)
        self.state.player.transport.option_id = transport_id
        self.state.player.transport.months_owned = 0
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

    def change_wealth_strategy(self, wealth_strategy_id: str) -> None:
        if wealth_strategy_id == self.state.player.wealth_strategy_id:
            raise ValueError("That wealth strategy is already selected.")
        strategy = get_wealth_strategy(self.bundle, wealth_strategy_id)
        self.state.player.wealth_strategy_id = wealth_strategy_id
        append_log(self.state, f"Wealth strategy set: {strategy.name}")
        trim_logs(self.bundle, self.state)

    def build_crisis_warnings(self) -> list[str]:
        player = self.state.player
        warnings: list[str] = []
        if player.debt >= self.state.debt_game_over_threshold * self.bundle.config.crisis_warning_debt_ratio:
            warnings.append("Debt is getting close to collections.")
        if player.stress >= self.bundle.config.crisis_warning_stress:
            warnings.append("Stress is getting close to burnout territory.")
        if player.energy <= self.bundle.config.crisis_warning_energy:
            warnings.append("Energy is dangerously low.")
        if player.housing.missed_payment_streak >= self.bundle.config.crisis_warning_housing_streak:
            warnings.append("Housing stability is wobbling.")
        if player.education.failure_streak >= max(1, self.state.academic_failure_streak_limit - 1):
            warnings.append("School pressure is close to a hard setback.")
        if player.housing.housing_stability <= 40:
            warnings.append("Housing stability is sliding and may cascade into stress.")
        if player.transport.reliability_score <= 45:
            warnings.append("Transport reliability is now threatening your work consistency.")
        if player.career.transition_penalty_months > 0:
            warnings.append("Career transition drag is still active.")
        return warnings

    def build_month_outlook(self) -> list[str]:
        player = self.state.player
        city = get_city(self.bundle, self.state.player.current_city_id)
        housing = get_housing_option(self.bundle, player.housing_id)
        transport = get_transport_option(self.bundle, player.transport_id)
        track = get_career_track(self.bundle, player.career.track_id)
        tier = get_current_career_tier(self.bundle, self.state)
        wealth_strategy = get_wealth_strategy(self.bundle, player.wealth_strategy_id)
        outlook = [
            f"{city.name}: {city.opportunity_text}",
            f"Pressure: {city.pressure_text}",
            f"Current lane: {tier.label} in {track.name}.",
            f"Wealth plan: {wealth_strategy.name}.",
        ]
        outlook.extend(f"Warning: {warning}" for warning in self.build_crisis_warnings())
        if housing.id == "parents" and player.family_support <= self.state.minimum_parent_fallback_support + 10:
            outlook.append("Staying home is still powerful money-wise, but the family buffer is thinning.")
        if housing.id == "roommates":
            outlook.append("Roommates keep costs down but can still crack the month sideways.")
        if transport.id in {"beater_car", "financed_car"}:
            outlook.append("Your transport is buying access, but it is also putting monthly pressure on you.")
        if transport.access_level < track.minimum_transport_access:
            outlook.append("Transport is limiting your current career ceiling.")
        if player.education.is_active and player.education.college_gpa < 2.7 and player.education.program_id in {"part_time_college", "full_time_university"}:
            outlook.append("Your GPA is below the stronger office/professional thresholds right now.")
        if player.education.is_active and player.education.standing < 55:
            outlook.append("School is slipping and could slow your long-term upside.")
        blockers = promotion_blockers(self.bundle, self.state)
        if blockers:
            outlook.append("Promotion gate: " + blockers[0])
        blocked_careers = [status for status in self.career_entry_statuses() if not status[2]]
        if blocked_careers:
            name, _, _, reason = blocked_careers[0]
            outlook.append(f"Career lockout: {name} - {reason}")
        outlook.append(
            f"Trajectory: momentum {player.career.promotion_momentum}, housing stability {player.housing.housing_stability}, "
            f"transport reliability {player.transport.reliability_score}."
        )
        outlook.append(f"Market regime: {self.state.current_market_regime_id.replace('_', ' ')}.")
        if self.state.active_modifiers:
            outlook.append("Active pressure: " + ", ".join(modifier.label for modifier in self.state.active_modifiers))
        if not self.state.active_modifiers and not eligible_events(self.bundle, self.state):
            outlook.append("Quiet month. Your own choices will shape most of the pressure.")
        if self.state.player.career.transition_penalty_months > 0:
            outlook.append("Career transition drag is still reducing this month's reliability.")
        if self.state.player.education.reentry_drag_months > 0:
            outlook.append("Education re-entry drag is slowing school momentum this month.")
        return outlook[:8]

    def is_finished(self) -> bool:
        return self.state.game_over_reason is not None or self.state.current_month > self.state.total_months
