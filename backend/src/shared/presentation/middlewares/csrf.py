"""Double-submit CSRF (ADR-004): toda mutación con sesión exige el header
`X-CSRF-Token` igual a la cookie `hdm_csrf`. El login emite esa cookie y el
http-client del frontend la reenvía desde siempre, pero hasta la auditoría de
seguridad del 2026-09-30 nadie la comparaba: solo protegía SameSite=Lax, que deja
pasar formularios desde otros puertos del mismo host o de *.cdsa.com.ar.

Sin cookie de sesión no se exige: login, olvidé/resetear contraseña y health no
tienen sesión que abusar, y cualquier otro endpoint responde 401 igual."""

import hmac
from collections.abc import Awaitable, Callable

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

_METODOS_SEGUROS = frozenset({"GET", "HEAD", "OPTIONS"})
_HEADER = "X-CSRF-Token"


class CsrfMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, session_cookie: str, csrf_cookie: str) -> None:
        super().__init__(app)
        self._session_cookie = session_cookie
        self._csrf_cookie = csrf_cookie

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method in _METODOS_SEGUROS or self._session_cookie not in request.cookies:
            return await call_next(request)
        esperado = request.cookies.get(self._csrf_cookie, "")
        recibido = request.headers.get(_HEADER, "")
        if esperado and hmac.compare_digest(esperado, recibido):
            return await call_next(request)
        return JSONResponse(
            status_code=403,
            content={
                "message": "Sesión inválida para esta acción: recargá la página o volvé a entrar",
                "code": "CSRF_INVALIDO",
                "details": None,
            },
        )
