from dataclasses import dataclass
from math import isclose, isfinite


@dataclass(frozen=True)
class Weights:
    skills: float = 0.50
    experience: float = 0.25
    location: float = 0.15
    work_mode: float = 0.10

    def __post_init__(self) -> None:
        values = (self.skills, self.experience, self.location, self.work_mode)
        if any(not isfinite(v) or not 0 <= v <= 1 for v in values):
            raise ValueError("Los pesos deben ser finitos entre 0 y 1.")
        if not isclose(sum(values), 1.0, rel_tol=0, abs_tol=1e-9):
            raise ValueError("Los pesos deben sumar 1.")
