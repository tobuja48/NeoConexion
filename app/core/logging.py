import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.core.exceptions import error_response


def configure_logging(level: str) -> None:
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    # Driver DEBUG logs can contain query parameters. Never enable them via LOG_LEVEL.
    logging.getLogger("neo4j").setLevel(logging.CRITICAL)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").disabled = True


def install_request_logging(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_logging(request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.request_id = uuid4().hex
        started = perf_counter()
        status = 500
        try:
            try:
                response = await call_next(request)
            except Exception as exc:
                # Avoid Starlette re-raising a handled failure into uvicorn's traceback logger.
                logging.getLogger("neoconexion").error(
                    "internal_error request_id=%s type=%s", request.state.request_id,
                    type(exc).__name__,
                )
                response = error_response(request, "INTERNAL_ERROR", "Error interno del servidor.", 500)
            status = response.status_code
            response.headers["X-Request-ID"] = request.state.request_id
            return response
        finally:
            # Log route templates, never raw URLs, IDs, payloads, or headers.
            route = getattr(request.scope.get("route"), "path", "unmatched")
            logging.getLogger("neoconexion").info(
                "request_id=%s method=%s route=%s status=%s duration_ms=%.1f",
                request.state.request_id, request.method, route, status,
                (perf_counter() - started) * 1000,
            )
