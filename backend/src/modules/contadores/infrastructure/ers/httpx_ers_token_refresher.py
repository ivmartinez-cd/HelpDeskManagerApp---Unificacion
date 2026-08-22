"""Renovación del Bearer token de Epson Remote Services (ERS).

Reemplaza al login con Playwright headless que usaba la app legacy
(HelpDeskManager-Web): dentro de Docker el desafío anti-bot de Incapsula hacía el
login lento e intermitente, y resultó innecesario — el endpoint de auth no está
detrás del WAF y acepta las credenciales directamente.

El JSON guardado mantiene el formato del refresher viejo ({token, cookies,
updated_at, username}) para que `_build_session` del provider siga funcionando
sin cambios; `cookies` queda vacío porque la API de ERS solo exige el Bearer.
"""
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx

from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import Settings, get_settings

# La SPA de ERS (Nuxt) se autentica contra el Auth de Epson Cloud Platform con
# un OAuth2 password grant. Este Basic es el client_id:client_secret PÚBLICO
# embebido en el bundle JS de www.remote-services.epson.com — no es un secreto
# nuestro, es el identificador del cliente web oficial de Epson. Capturado
# observando el POST que hace la SPA al loguearse.
_AUTH_URL = "https://auth-api.cp.epson.com/oauth2/auth/token/?subject=user"
_CLIENT_BASIC = (
    "Basic M2JhMjdjOGM1OWJkNDhiZGI0YTBhYWMzNjg1NDRlZGI6NmVlYmNnczVIWk1IWjBJWVNw"
    "WjZyd1F4bUt4U3BEQmVLSWU3Zk96c29ycGg1ZVNTMU1HWU9GMTVrdVZiQUh6ZA=="
)
_AUTH_HEADERS = {
    "authorization": _CLIENT_BASIC,
    "content-type": "application/x-www-form-urlencoded",
}


async def refresh_ers_token(
    token_file_path: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Obtiene un Bearer token de ERS con el mismo OAuth2 password grant que
    usa la SPA oficial y lo guarda en `token_file_path`."""
    username, password = _require_credentials(settings or get_settings())
    access_token = await _request_access_token(username, password)
    token_data: dict[str, Any] = {
        "token": f"Bearer {access_token}",
        "cookies": [],
        "updated_at": datetime.now(UTC).isoformat(),
        "username": username,
    }
    _persist_token(token_data, Path(token_file_path))
    return token_data


def _require_credentials(cfg: Settings) -> tuple[str, str]:
    username = cfg.epson_ers_username
    password = cfg.epson_ers_password.get_secret_value()
    if not username or not password:
        raise ExternalServiceError(
            "Faltan credenciales de ERS (EPSON_ERS_USERNAME/EPSON_ERS_PASSWORD)."
        )
    return username, password


async def _request_access_token(username: str, password: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                _AUTH_URL,
                headers=_AUTH_HEADERS,
                data={"grant_type": "password", "username": username, "password": password},
            )
    except Exception as exc:
        raise ExternalServiceError(
            f"No se pudo conectar al servicio de autenticación de ERS: {exc}"
        ) from exc
    if resp.status_code != 200:
        raise ExternalServiceError(
            f"Fallo el login de ERS ({resp.status_code}). Verificá las credenciales."
        )
    access_token = resp.json().get("access_token")
    if not access_token:
        raise ExternalServiceError("El login de ERS no devolvió un access_token.")
    return cast(str, access_token)


def _persist_token(token_data: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=2)
