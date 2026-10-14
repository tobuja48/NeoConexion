from app.domain.matching.normalization import key

def location_score(candidate_location: str, job_location: str, job_mode: str) -> float:
    return 100.0 if key(job_mode) == "remote" or key(candidate_location) == key(job_location) else 0.0

def work_mode_score(preferred: str, offered: str) -> float:
    modes = {key(preferred), key(offered)}
    return 100.0 if len(modes) == 1 or "any" in modes else 50.0 if "hybrid" in modes else 0.0
