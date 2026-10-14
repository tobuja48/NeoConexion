def experience_score(years: float, required: float) -> float:
    """Finite nonnegative values are guaranteed by the public schema."""
    return 100.0 if required == 0 else min(1.0, years / required) * 100
