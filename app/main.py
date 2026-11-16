from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from app.core.neo4j_driver import close_driver, get_driver
from app.core.config import get_settings
from app.core.exceptions import register_handlers
from app.core.logging import configure_logging, install_request_logging
from app.core.visualization import VisualizationMiddleware
from app.repositories.schema_setup import setup_schema
from app.api.v1.router import router
from app.schemas.common import ERROR_RESPONSES, HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        configure_logging(get_settings().log_level)
        await run_in_threadpool(get_driver().verify_connectivity)
        await run_in_threadpool(setup_schema, get_driver())
        yield
    finally:
        await run_in_threadpool(close_driver)


app = FastAPI(
    title="NeoConexión", version="0.1.0", lifespan=lifespan,
    description=("API de matching interpretable entre candidatos y vacantes. "
                 "Upserts por ID externo; recomendaciones basadas en habilidades, experiencia, "
                 "ubicación y modalidad. X-API-Key solo se exige si API_KEY está configurada."),
)
register_handlers(app)
install_request_logging(app)
app.add_middleware(VisualizationMiddleware)
app.include_router(router)
app.mount("/app", StaticFiles(directory=Path(__file__).parent / "web", html=True), name="conecta")


def install_cors(app: FastAPI, origins: list[str]) -> None:
    """Permite que frontends de navegador consuman la API. Se añade al final para quedar
    como middleware más externo y que también los errores lleven cabeceras CORS."""
    if not origins:
        return
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )


install_cors(app, get_settings().cors_origin_list)


@app.get("/health", tags=["Health"], response_model=HealthResponse,
         summary="Verificar proceso API")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db", tags=["Health"], response_model=HealthResponse,
         responses=ERROR_RESPONSES, summary="Verificar conexión con Neo4j")
def health_db() -> dict[str, str]:
    get_driver().verify_connectivity()
    return {"status": "ok"}
