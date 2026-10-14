from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel

Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Skill = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
NonNegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class PublicModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True,
                              str_strip_whitespace=True, extra="forbid")


class WorkMode(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class PreferredWorkMode(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    ANY = "any"


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: str = "ok"


ERROR_RESPONSES = {status: {"model": ErrorResponse, "description": description}
                   for status, description in [(404, "Recurso no encontrado"),
                   (422, "Solicitud inválida"), (401, "API Key inválida"),
                   (503, "Base de datos no disponible"), (500, "Error interno")]}
