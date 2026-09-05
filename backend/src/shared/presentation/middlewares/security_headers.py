"""Headers de seguridad HTTP en toda respuesta del backend.

La app corre detrás de un proxy inverso en la red corporativa; estos headers
son la línea base que no depende de cómo esté configurado ese proxy (ronda E2E
2026-09-05: no había ninguno). `setdefault` respeta lo que un endpoint ya haya
fijado (p. ej. `Cache-Control` de un export)."""

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

_HEADERS_BASE = (
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "same-origin"),
    ("Permissions-Policy", "camera=(), microphone=(), geolocation=()"),
)
_HSTS = "max-age=31536000; includeSubDomains"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, hsts: bool) -> None:
        super().__init__(app)
        self._hsts = hsts

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for nombre, valor in _HEADERS_BASE:
            response.headers.setdefault(nombre, valor)
        if request.url.path.startswith("/api/"):
            # Respuestas de API con sesión: que ningún cache intermedio las guarde.
            response.headers.setdefault("Cache-Control", "no-store")
        if self._hsts:
            response.headers.setdefault("Strict-Transport-Security", _HSTS)
        return response
