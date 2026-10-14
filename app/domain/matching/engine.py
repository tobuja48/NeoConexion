from app.domain.matching.models import Breakdown, Candidate, Job, MatchResult
from app.domain.matching.normalization import key
from app.domain.matching.weights import Weights
from app.domain.matching.skills import skill_coverage
from app.domain.matching.experience import experience_score
from app.domain.matching.preferences import location_score, work_mode_score


def score(candidate: Candidate, job: Job, weights: Weights) -> MatchResult:
    """Score one pair without IO; missingSkills contains mandatory skills only."""
    coverage = skill_coverage(candidate.skills, job.required_skills, job.desired_skills)
    skills = coverage.score
    required_count, desired_count = coverage.required_count, coverage.desired_count
    required = range(coverage.required_total)
    desired = range(coverage.desired_total)
    missing, matches = coverage.missing, coverage.matching
    experience = experience_score(candidate.years_of_experience, job.required_experience)
    remote = key(job.work_mode) == "remote"
    same_location = key(candidate.location) == key(job.location)
    location = location_score(candidate.location, job.location, job.work_mode)
    work_mode = work_mode_score(candidate.preferred_work_mode, job.work_mode)
    total = (skills * weights.skills + experience * weights.experience +
             location * weights.location + work_mode * weights.work_mode)
    explanations = [f"Cumple {required_count} de {len(required)} habilidades obligatorias"
                    if required else "La vacante no exige habilidades obligatorias"]
    if desired:
        explanations.append(f"Cumple {desired_count} de {len(desired)} habilidades deseables")
    if missing:
        explanations.append("Habilidades obligatorias faltantes: " + ", ".join(missing))
    explanations.append(
        f"Experiencia {'suficiente' if experience == 100 else 'insuficiente'} "
        f"({candidate.years_of_experience:g} años vs {job.required_experience:g} requeridos)"
    )
    explanations.append("Vacante remota: ubicación compatible" if remote else
                        "Ubicación coincidente" if same_location else "Ubicación diferente")
    explanations.append({100.0: "Modalidad de trabajo compatible", 50.0:
                         "Modalidad parcialmente compatible por trabajo híbrido", 0.0:
                         "Modalidad de trabajo incompatible"}[work_mode])
    return MatchResult(round(total, 1), Breakdown(skills, experience, location, work_mode),
                       matches, missing, tuple(explanations))
