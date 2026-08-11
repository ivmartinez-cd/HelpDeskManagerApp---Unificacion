import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import Settings, get_settings

# gestion.cdsa.com.ar es una app Symfony con form_login estándar, sin WAF ni
# anti-bot de por medio (a diferencia de ERS) — confirmado logueándose de
# verdad: GET /login trae el _csrf_token atado a la sesión anónima, POST
# /login_check con usuario+contraseña+token autentica esa misma sesión.
_CSRF_TOKEN_RE = re.compile(r'name="_csrf_token"\s+value="([^"]+)"')


async def refresh_gestion_session(
    session_file_path: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Hace login contra gestion.cdsa.com.ar y guarda el PHPSESSID resultante
    en `session_file_path`, reemplazando el cookie que antes se pegaba a mano
    en GESTION_WEB_COOKIE cada vez que vencía."""
    cfg = settings or get_settings()
    username = cfg.gestion_web_username
    password = cfg.gestion_web_password.get_secret_value()
    if not username or not password:
        raise ExternalServiceError(
            "Faltan credenciales de Gestión (GESTION_WEB_USERNAME/GESTION_WEB_PASSWORD)."
        )

    session_id = await _login(
        cfg.gestion_web_base_url, username, password, cfg.gestion_web_timeout_seconds
    )
    return _persist_session(session_file_path, session_id, username)


async def _login(base_url: str, username: str, password: str, timeout: float) -> str:
    url = base_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            login_page = await client.get(f"{url}/login")
            match = _CSRF_TOKEN_RE.search(login_page.text)
            if not match:
                raise ExternalServiceError(
                    "No se encontró el _csrf_token en /login de Gestión "
                    "(¿cambió el formulario?)."
                )
            resp = await client.post(
                f"{url}/login_check",
                data={
                    "_username": username,
                    "_password": password,
                    "_csrf_token": match.group(1),
                },
            )
            session_id = client.cookies.get("PHPSESSID")
    except ExternalServiceError:
        raise
    except Exception as exc:
        raise ExternalServiceError(f"No se pudo conectar al login de Gestión: {exc}") from exc

    if resp.status_code not in (301, 302, 303) or not session_id:
        raise ExternalServiceError(
            f"Fallo el login de Gestión ({resp.status_code}). Verificá usuario y contraseña."
        )
    return session_id


def _persist_session(session_file_path: str, session_id: str, username: str) -> dict[str, Any]:
    out_path = Path(session_file_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    session_data: dict[str, Any] = {
        "cookie": f"theme=dark; PHPSESSID={session_id}",
        "updated_at": datetime.now(UTC).isoformat(),
        "username": username,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)
    return session_data
