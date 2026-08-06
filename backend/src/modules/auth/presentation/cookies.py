from fastapi import Response

from src.shared.infrastructure.config.settings import get_settings

# Path=/ para las dos, no solo /api: el proxy.ts del frontend (Etapa 12)
# necesita leer hdm_session en CUALQUIER ruta (ej. "/") para decidir si
# redirige a /login — con Path=/api el browser ni la manda ahí. httpOnly ya
# la esconde del JS de la página; acotar el Path no sumaba seguridad real,
# solo rompía el caso de uso del proxy.
_SESSION_PATH = "/"
_CSRF_PATH = "/"
_MAX_AGE_SECONDS = 7 * 24 * 3600


def set_session_cookies(response: Response, *, session_token: str, csrf_token: str) -> None:
    """ADR-004: `hdm_session` httpOnly (el JS de la página nunca la ve),
    `hdm_csrf` legible a propósito (double-submit contra CSRF, Etapa 15)."""
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        max_age=_MAX_AGE_SECONDS,
        path=_SESSION_PATH,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=_MAX_AGE_SECONDS,
        path=_CSRF_PATH,
        httponly=False,
        samesite="lax",
        secure=settings.session_cookie_secure,
    )


def clear_session_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(key=settings.session_cookie_name, path=_SESSION_PATH)
    response.delete_cookie(key=settings.csrf_cookie_name, path=_CSRF_PATH)
