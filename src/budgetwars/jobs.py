"""Job utilities placeholder."""

from __future__ import annotations

from .models import JobDefinition


def job_map(jobs: list[JobDefinition]) -> dict[str, JobDefinition]:
    return {job.id: job for job in jobs}
