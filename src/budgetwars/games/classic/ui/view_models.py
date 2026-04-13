from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _SetupGroup:
    key: str
    title: str
    prompt: str
    options: list[tuple[str, str, str]]
    initial_id: str | None


@dataclass(frozen=True)
class BuildSystemVM:
    system: str
    primary: str
    detail: str | None = None
    progress: str | None = None
    tone: str = "neutral"

    @property
    def label(self) -> str:
        return self.system

    @property
    def value(self) -> str:
        return self.primary


@dataclass(frozen=True)
class BuildSnapshotVM:
    player_name: str
    city_name: str
    identity_line: str | None = None
    persistent_commitments: list[str] = field(default_factory=list)
    items: list[BuildSystemVM] = field(default_factory=list)

    @property
    def headline(self) -> str:
        return f"{self.player_name} in {self.city_name}"

    @property
    def systems(self) -> list[BuildSystemVM]:
        return self.items


@dataclass(frozen=True)
class MonthlyForecastVM:
    monthly_focus: str
    main_threat: str
    best_opportunity: str
    chosen_focus: str
    expected_swing: str
    situation_family: str
    credit_status: str
    progress_label: str
    progress_detail: str
    progress_fraction: float
    persistent_commitments: list[str] = field(default_factory=list)
    active_status_arcs: list["StatusArcVM"] = field(default_factory=list)
    recovery_route: str | None = None
    blocked_doors: list[str] = field(default_factory=list)
    driver_notes: list[str] = field(default_factory=list)
    recent_summary: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PressureMetricVM:
    label: str
    primary: str
    detail: str | None = None
    tone: str = "neutral"


@dataclass(frozen=True)
class StatusArcVM:
    arc_id: str
    name: str
    summary: str
    severity: int
    months_remaining: int
    tone: str = "warning"
    resolution_hint: str | None = None
    blocked_door_hints: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PressureSummaryVM:
    projected_score: float
    score_tier: str
    biggest_risk: str
    credit_score: int
    credit_tier: str
    credit_progress_label: str
    credit_progress_detail: str
    credit_progress_fraction: float
    progress_label: str
    progress_detail: str
    progress_fraction: float
    run_killer: str = ""
    fastest_fix: str = ""
    pressure_family: str = ""
    month_driver: str = ""
    active_status_arcs: list[StatusArcVM] = field(default_factory=list)
    recovery_route: str | None = None
    persistent_commitments: list[str] = field(default_factory=list)
    blocked_doors: list[str] = field(default_factory=list)
    pending_fallout_count: int = 0
    pending_decisions: list[str] = field(default_factory=list)
    primary_metrics: list[PressureMetricVM] = field(default_factory=list)
    secondary_metrics: list[PressureMetricVM] = field(default_factory=list)
    active_modifiers: list[str] = field(default_factory=list)
    crisis_watch: list[str] = field(default_factory=list)

    @property
    def tier(self) -> str:
        return self.score_tier


@dataclass(frozen=True)
class ScoreDeltaVM:
    previous_score: float | None
    current_score: float
    delta: float
    previous_tier: str | None
    tier: str
    strongest_category: str
    weakest_category: str
    diagnosis: str

    @property
    def prev_score(self) -> float | None:
        return self.previous_score

    @property
    def prev_tier(self) -> str | None:
        return self.previous_tier


@dataclass(frozen=True)
class LearnTopicVM:
    id: str
    title: str
    what_it_is: str
    how_to_raise: list[str] = field(default_factory=list)
    how_to_lower: list[str] = field(default_factory=list)
    why_it_matters: list[str] = field(default_factory=list)
    common_drivers: list[str] = field(default_factory=list)
    related_situation_families: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LearnDrawerVM:
    active_pressure_family: str
    credit_line: str
    stress_line: str
    pressure_sources: list[str] = field(default_factory=list)
    topics: list[LearnTopicVM] = field(default_factory=list)
