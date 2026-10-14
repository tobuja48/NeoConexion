import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from neo4j.exceptions import DriverError, Neo4jError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

logger = logging.getLogger("neoconexion")


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int, details: Any = None) -> None:
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details


class NotFound(AppError):
    def __init__(self, entity: str) -> None:
        super().__init__("NOT_FOUND", f"{entity} no encontrado.", 404)


def error_response(request: Request, code: str, message: str, status: int,
                   details: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details}},
        headers={"X-Request-ID": getattr(request.state, "request_id", "")},
    )


def register_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def application_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(request, exc.code, exc.message, exc.status, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Do not echo input values or Pydantic contexts containing personal data.
        details = [{"loc": list(e["loc"]), "type": e["type"]} for e in exc.errors()]
        return error_response(request, "VALIDATION_ERROR", "Solicitud inválida.", 422, details)

    @app.exception_handler(DriverError)
    @app.exception_handler(Neo4jError)
    async def database_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error("database_error request_id=%s type=%s",
                     request.state.request_id, type(exc).__name__)
        return error_response(request, "DB_UNAVAILABLE", "Base de datos no disponible.", 503)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "VALIDATION_ERROR"
        return error_response(request, code, "Recurso no encontrado." if code == "NOT_FOUND"
                              else "Solicitud no permitida.", exc.status_code)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error("internal_error request_id=%s type=%s",
                     request.state.request_id, type(exc).__name__)
        return error_response(request, "INTERNAL_ERROR", "Error interno del servidor.", 500)
