"""Login del wsAyC securitizado (sep-2026, port del legacy SDSInsumos).

CDS securitizó wsg.cdsisa.com.ar: toda operación exige un token JWT (~8 h de vida)
obtenido con `login()` usando un usuario de servicios web (id_tipo = 11 del lado de
CDS, distinto del usuario de WebAgentes), y una ACL por usuario define qué métodos
puede invocar. El token es uno por proceso y se renueva bajo lock: el scan de
insumos dispara llamadas en paralelo que pueden encontrarlo vencido a la vez.

Tras un login rechazado no se reintenta por `_LOGIN_COOLDOWN_SECONDS`: cada llamada
en paralelo intentaría su propio login fallido (riesgo de bloqueo del usuario).
"""

import json
import logging
import threading
import time
from collections.abc import Callable

from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)

_LOGIN_COOLDOWN_SECONDS = 300.0
_TOKEN_KEYS = ("token", "Token", "access_token", "jwt")

LoginFn = Callable[[str, str], object]


class WsAycAuthError(ExternalServiceError):
    """El wsAyC rechazó el login (credenciales mal o usuario sin permiso de servicios web)."""

    default_code = "WSAYC_AUTH_ERROR"


def _parse_login_response(raw: object) -> dict[str, object]:
    try:
        parsed = json.loads(str(raw))
    except ValueError:
        parsed = None
    if not isinstance(parsed, dict):
        raise WsAycAuthError("Respuesta inesperada del login del web service wsAyC (no es JSON)")
    return parsed


def extract_token(raw: object) -> str:
    """Saca el token de la respuesta de login(): un JSON dentro de un string SOAP.

    Error conocido: {"status":"ERROR","message":"Credenciales invalidas ..."}.
    """
    parsed = _parse_login_response(raw)
    if str(parsed.get("status", "")).upper() == "ERROR":
        raise WsAycAuthError(
            f"Login al web service wsAyC rechazado: {parsed.get('message', 'sin detalle')} "
            "— verificar WSAYC_USERNAME / WSAYC_PASSWORD"
        )
    for container in (parsed, parsed.get("data"), parsed.get("Respuesta")):
        if isinstance(container, dict):
            for key in _TOKEN_KEYS:
                if container.get(key):
                    return str(container[key])
    # Sin loguear la respuesta entera: si el token viniera con otra key, quedaría en el log.
    raise WsAycAuthError(
        f"El login del web service wsAyC no devolvió token (keys: {sorted(parsed)})"
    )


class WsAycTokenManager:
    def __init__(self, username: str, password: str, login: LoginFn) -> None:
        self._username = username
        self._password = password
        self._login = login
        self._lock = threading.Lock()
        self._token: str | None = None
        self._login_error: tuple[float, WsAycAuthError] | None = None

    def current(self) -> str:
        token = self._token
        return token if token is not None else self.renew(None)

    def renew(self, stale: str | None) -> str:
        """Pide un token nuevo, salvo que otro thread ya lo haya renovado mientras esperábamos."""
        with self._lock:
            if self._token is not None and self._token != stale:
                return self._token
            self._raise_if_cooling_down()
            try:
                token = self._fetch_token()
            except WsAycAuthError as exc:
                self._login_error = (time.monotonic(), exc)
                logger.error("wsAyC: login rechazado", extra={"wsayc_user": self._username})
                raise
            self._login_error = None
            self._token = token
            logger.info("wsAyC: login OK, token renovado")
            return token

    def _raise_if_cooling_down(self) -> None:
        if self._login_error is None:
            return
        failed_at, exc = self._login_error
        if time.monotonic() - failed_at < _LOGIN_COOLDOWN_SECONDS:
            raise exc

    def _fetch_token(self) -> str:
        if not self._username or not self._password:
            raise WsAycAuthError(
                "Faltan WSAYC_USERNAME / WSAYC_PASSWORD para el web service wsAyC "
                "(ver .env.example)"
            )
        return extract_token(self._login(self._username, self._password))
