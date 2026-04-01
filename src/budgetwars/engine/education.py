from __future__ import annotations

from budgetwars.models import ContentBundle, EducationProgramDefinition, GameState

from .effects import append_log
from .lookups import get_education_program


def can_switch_education(bundle: ContentBundle, state: GameState, program_id: str) -> tuple[bool, str]:
    program = get_education_program(bundle, program_id)
    current = state.player.education
    if program_id == current.program_id:
        return True, ""
    if state.player.opening_path_id not in program.entry_path_ids:
        return False, "That program is not open from your current life lane."
    if state.player.academic_strength < program.minimum_academic_strength:
        return False, "Your academic footing is too weak for that program right now."
    return True, ""


def education_monthly_cost(bundle: ContentBundle, state: GameState, *, modifier_delta: int = 0) -> int:
    program = get_education_program(bundle, state.player.education.program_id)
    if not state.player.education.is_active or program.id == "none":
        return 0
    city = next(item for item in bundle.cities if item.id == state.player.current_city_id)
    difficulty = next(item for item in bundle.difficulties if item.id == state.difficulty_id)
    cost = program.monthly_cost * city.education_cost_multiplier * difficulty.education_cost_multiplier
    return max(0, int(round(cost + modifier_delta)))


def apply_education_effects(bundle: ContentBundle, state: GameState) -> EducationProgramDefinition:
    program = get_education_program(bundle, state.player.education.program_id)
    if not state.player.education.is_active or program.id == "none":
        return program
    state.player.stress += program.monthly_stress
    state.player.energy += program.monthly_energy_delta
    return program


def update_education_progress(bundle: ContentBundle, state: GameState, progress_bonus: int) -> None:
    program = get_education_program(bundle, state.player.education.program_id)
    education = state.player.education
    if not education.is_active or program.id == "none":
        return

    standing_delta = 0
    if state.player.academic_strength >= 70:
        standing_delta += 2
    elif state.player.academic_strength <= 50:
        standing_delta -= 2
    if state.player.stress >= 75:
        standing_delta -= 5
    if state.player.energy <= 25:
        standing_delta -= 4
    if state.player.selected_focus_action_id == "study_push":
        standing_delta += 3
    if state.player.selected_focus_action_id == "overtime":
        standing_delta -= 1
    if state.player.selected_focus_action_id == "recovery_month":
        standing_delta -= 1

    education.standing = max(0, min(100, education.standing + standing_delta))

    if program.uses_gpa:
        gpa_delta = 0.0
        if state.player.academic_strength >= 75:
            gpa_delta += 0.06
        elif state.player.academic_strength <= 55:
            gpa_delta -= 0.05
        if state.player.stress >= 75:
            gpa_delta -= 0.11
        elif state.player.stress >= 60:
            gpa_delta -= 0.05
        if state.player.energy <= 25:
            gpa_delta -= 0.1
        elif state.player.energy <= 40:
            gpa_delta -= 0.04
        if state.player.selected_focus_action_id == "study_push":
            gpa_delta += 0.08
        elif state.player.selected_focus_action_id == "overtime":
            gpa_delta -= 0.04
        education.college_gpa = max(0.0, min(4.0, education.college_gpa + gpa_delta))

    if education.standing < 45:
        education.failure_streak += 1
        state.player.stress += 4
        state.player.life_satisfaction -= 3
        education.months_completed = max(0, education.months_completed - 1)
        if program.uses_gpa:
            education.college_gpa = max(0.0, education.college_gpa - 0.08)
        append_log(state, "School slipped badly this month and your progress took a real hit.")
        return

    education.failure_streak = 0
    progress_gain = max(0, 1 + progress_bonus)
    education.months_completed += progress_gain
    if program.duration_months > 0 and education.months_completed >= program.duration_months:
        education.months_completed = program.duration_months
        education.is_active = False
        education.is_paused = False
        if program.id not in education.completed_program_ids:
            education.completed_program_ids.append(program.id)
        if program.credential_id and program.credential_id not in education.earned_credential_ids:
            education.earned_credential_ids.append(program.credential_id)
        if program.pass_state_program:
            education.training_passed = True
        state.player.life_satisfaction += program.completion_life_satisfaction_bonus
        if program.id == "upgrading":
            state.player.academic_strength = min(100, state.player.academic_strength + 10)
            education.college_gpa = min(4.0, round(education.college_gpa + 0.2, 2))
        if program.uses_gpa:
            append_log(state, f"You completed {program.name} with a {education.college_gpa:.2f} GPA.")
        else:
            append_log(state, f"You completed {program.name} and opened a new credential lane.")
