import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.shared.domain.errors import AppError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unexpected_error)


def _envelope(message: str, code: str, details: object | None = None) -> dict[str, object]:
    return {"message": message, "code": code, "details": details}


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    logger.warning(
        "Handled application error",
        extra={"request_id": _request_id(request), "code": exc.code},
    )
    content = _envelope(exc.message, exc.code, exc.details)
    return JSONResponse(status_code=exc.http_status, content=content)


async def _handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = [
        {"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()
    ]
    content = _envelope("Error de validación", "VALIDATION_ERROR", details)
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=content)


async def _handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    content = _envelope(str(exc.detail), "HTTP_ERROR", None)
    return JSONResponse(status_code=exc.status_code, content=content)


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception", extra={"request_id": _request_id(request)})
    content = _envelope("Error interno del servidor", "INTERNAL_ERROR", None)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)
