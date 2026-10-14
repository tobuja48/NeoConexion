from pydantic import Field
from app.schemas.common import PublicModel
from app.schemas.job import JobSchema


class JobCatalog(PublicModel):
    total: int = Field(ge=0, description="Ofertas que cumplen los filtros antes de paginar")
    limit: int = Field(ge=1, le=50)
    offset: int = Field(ge=0)
    items: list[JobSchema]
