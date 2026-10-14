from dataclasses import dataclass
from app.domain.matching.normalization import key, unique_names

@dataclass(frozen=True)
class SkillCoverage:
    score: float
    matching: tuple[str, ...]
    missing: tuple[str, ...]
    required_count: int
    required_total: int
    desired_count: int
    desired_total: int

def skill_coverage(owned: tuple[str, ...], required: tuple[str, ...],
                   desired: tuple[str, ...]) -> SkillCoverage:
    keys = {key(s) for s in owned}
    mandatory = unique_names(required)
    mandatory_keys = {key(s) for s in mandatory}
    optional = tuple(s for s in unique_names(desired) if key(s) not in mandatory_keys)
    missing = tuple(s for s in mandatory if key(s) not in keys)
    matches = tuple(s for s in (*mandatory, *optional) if key(s) in keys)
    mandatory_hits = len(mandatory) - len(missing)
    optional_hits = sum(key(s) in keys for s in optional)
    value = 100.0
    if mandatory:
        value = 100 * mandatory_hits / len(mandatory)
        if optional:
            value = value * 0.7 + 30 * optional_hits / len(optional)
    return SkillCoverage(value, matches, missing, mandatory_hits, len(mandatory),
                         optional_hits, len(optional))
