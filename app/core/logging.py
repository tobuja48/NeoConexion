import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.exceptions import error_response


def configure_logging(level: str) -> None:
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    # Driver DEBUG logs can contain query parameters. Never enable them via LOG_LEVEL.
    logging.getLogger("neo4j").setLevel(logging.CRITICAL)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").disabled = True


class RequestLoggingMiddleware:
    """Log HTTP requests without a task/stream bridge around each response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        request.state.request_id = uuid4().hex
        started = perf_counter()
        status = 500
        response_started = False

        async def send_response(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                status = message["status"]
                MutableHeaders(scope=message)["X-Request-ID"] = request.state.request_id
                response_started = True
            await send(message)

        try:
            try:
                await self.app(scope, receive, send_response)
            except Exception as exc:
                # Avoid Starlette re-raising a handled failure into uvicorn's traceback logger.
                logging.getLogger("neoconexion").error(
                    "internal_error request_id=%s type=%s", request.state.request_id,
                    type(exc).__name__,
                )
                if response_started:
                    # An in-flight stream cannot be replaced with a second response.
                    raise
                response = error_response(request, "INTERNAL_ERROR", "Error interno del servidor.", 500)
                await response(scope, receive, send_response)
        finally:
            # Log route templates, never raw URLs, IDs, payloads, or headers.
            route = getattr(request.scope.get("route"), "path", "unmatched")
            logging.getLogger("neoconexion").info(
                "request_id=%s method=%s route=%s status=%s duration_ms=%.1f",
                request.state.request_id, request.method, route, status,
                (perf_counter() - started) * 1000,
            )


def install_request_logging(app: FastAPI) -> None:
    app.add_middleware(RequestLoggingMiddleware)
