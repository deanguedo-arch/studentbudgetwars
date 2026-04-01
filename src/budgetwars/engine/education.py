from __future__ import annotations

from budgetwars.models import ContentBundle, EducationProgramDefinition, GameState

from .effects import append_log
from .lookups import get_education_program


def can_switch_education(bundle: ContentBundle, state: GameState, program_id: str) -> tuple[bool, str]:
    program = get_education_program(bundle, program_id)
    if program_id == state.player.education.program_id and state.player.education.is_active == (program_id != "none"):
        return False, "You are already set up that way."
    if state.player.opening_path_id not in program.entry_path_ids:
        return False, "That program is not open from your starting path in this version."
    return True, ""


def education_monthly_cost(bundle: ContentBundle, state: GameState, *, modifier_delta: int = 0) -> int:
    program = get_education_program(bundle, state.player.education.program_id)
    if not state.player.education.is_active or program.id == "none":
        return 0
    return max(0, int(round(program.monthly_cost + modifier_delta)))


def apply_education_effects(bundle: ContentBundle, state: GameState) -> EducationProgramDefinition:
    program = get_education_program(bundle, state.player.education.program_id)
    if not state.player.education.is_active or program.id == "none":
        return program
    state.player.stress += program.monthly_stress
    state.player.energy += program.monthly_energy_delta
    return program


def update_education_progress(bundle: ContentBundle, state: GameState, progress_bonus: int) -> None:
    program = get_education_program(bundle, state.player.education.program_id)
    if not state.player.education.is_active or program.id == "none":
        return

    standing_delta = 0
    if state.player.academic_strength >= 70:
        standing_delta += 2
    elif state.player.academic_strength <= 55:
        standing_delta -= 1
    if state.player.stress >= 75:
        standing_delta -= 5
    if state.player.energy <= 25:
        standing_delta -= 4
    if state.player.selected_focus_action_id == "push_forward":
        standing_delta += 2
    if state.player.selected_focus_action_id == "recover":
        standing_delta -= 1

    state.player.education.standing = max(0, min(100, state.player.education.standing + standing_delta))

    if program.id == "college":
        gpa_delta = 0.0
        if state.player.academic_strength >= 75:
            gpa_delta += 0.06
        elif state.player.academic_strength <= 55:
            gpa_delta -= 0.05
        if state.player.stress >= 75:
            gpa_delta -= 0.12
        elif state.player.stress >= 60:
            gpa_delta -= 0.06
        if state.player.energy <= 25:
            gpa_delta -= 0.12
        elif state.player.energy <= 40:
            gpa_delta -= 0.05
        if state.player.selected_focus_action_id == "push_forward":
            gpa_delta += 0.08
        elif state.player.selected_focus_action_id == "stack_cash":
            gpa_delta -= 0.03
        state.player.education.college_gpa = max(0.0, min(4.0, state.player.education.college_gpa + gpa_delta))

    if state.player.education.standing < 45:
        state.player.stress += 4
        state.player.life_satisfaction -= 3
        state.player.education.months_completed = max(0, state.player.education.months_completed - 1)
        if program.id == "college":
            state.player.education.college_gpa = max(0.0, state.player.education.college_gpa - 0.08)
        append_log(state, "School slipped this month and your progress took a concrete hit.")
        return

    progress_gain = max(0, 1 + progress_bonus)
    state.player.education.months_completed += progress_gain
    if program.duration_months > 0 and state.player.education.months_completed >= program.duration_months:
        state.player.education.months_completed = program.duration_months
        state.player.education.is_active = False
        if program.id not in state.player.education.completed_program_ids:
            state.player.education.completed_program_ids.append(program.id)
        if program.credential_id and program.credential_id not in state.player.education.earned_credential_ids:
            state.player.education.earned_credential_ids.append(program.credential_id)
        state.player.life_satisfaction += program.completion_life_satisfaction_bonus
        if program.id == "college":
            append_log(state, f"You completed {program.name} with a {state.player.education.college_gpa:.2f} GPA.")
        else:
            append_log(state, f"You completed {program.name} and passed into the next stage.")
