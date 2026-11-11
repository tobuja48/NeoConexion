from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.core.visualization import traces

router = APIRouter(tags=["Visualización"])


@router.get("/visualization/requests", summary="Consultar actividad del visor JSON local")
def activity(response: Response, after: Annotated[int, Query(ge=0)] = 0) -> dict:
    response.headers["Cache-Control"] = "no-store"
    return traces.read(after)
