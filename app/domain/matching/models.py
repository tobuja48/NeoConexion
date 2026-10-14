from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    id: str
    name: str
    location: str
    years_of_experience: float
    skills: tuple[str, ...]
    preferred_work_mode: str
    expected_salary: float | None = None


@dataclass(frozen=True)
class Job:
    id: str
    company: str
    title: str
    location: str
    work_mode: str
    required_experience: float
    required_skills: tuple[str, ...]
    desired_skills: tuple[str, ...] = ()
    description: str | None = None


@dataclass(frozen=True)
class Breakdown:
    skills: float
    experience: float
    location: float
    work_mode: float


@dataclass(frozen=True)
class MatchResult:
    match_score: float
    breakdown: Breakdown
    matching_skills: tuple[str, ...]
    missing_skills: tuple[str, ...]
    explanations: tuple[str, ...]
