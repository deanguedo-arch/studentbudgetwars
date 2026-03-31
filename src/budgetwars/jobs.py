from __future__ import annotations

from .models import GameState, JobDefinition
from .utils import clamp


def job_map(jobs: list[JobDefinition]) -> dict[str, JobDefinition]:
    return {job.id: job for job in jobs}


def get_job(jobs: list[JobDefinition], job_id: str | None) -> JobDefinition | None:
    if job_id is None:
        return None
    return job_map(jobs).get(job_id)


def switch_job(
    state: GameState,
    jobs: list[JobDefinition],
    new_job_id: str,
    stress_penalty: int,
    sync_location_to_job: bool = True,
) -> GameState:
    target_job = get_job(jobs, new_job_id)
    if target_job is None:
        return state.model_copy(update={"message_log": [*state.message_log, f"Invalid job selection: {new_job_id}."]})

    if state.player.job_id == target_job.id:
        return state.model_copy(update={"message_log": [*state.message_log, f"Already working as {target_job.name}."]})

    player_updates = {
        "job_id": target_job.id,
        "stress": clamp(state.player.stress + stress_penalty, 0, state.max_stress),
    }
    if sync_location_to_job:
        player_updates["location_id"] = target_job.location_id

    player = state.player.model_copy(update=player_updates)
    location_text = f" Location set to {target_job.location_id}." if sync_location_to_job else ""
    return state.model_copy(
        update={
            "player": player,
            "message_log": [
                *state.message_log,
                f"Switched job to {target_job.name}. Stress +{stress_penalty}.{location_text}",
            ],
        }
    )
