"""Parsing puro del HTML del PortalWeb de SDS — sin I/O, sin estado."""

import re

_CSRF_TOKEN_RE = re.compile(r'name="__csrftoken"\s+value="([^"]+)"')
DELETE_SUCCESS_MARKER = "Los cambios se han guardado correctamente"
MAX_HTML_BYTES = 5 * 1024 * 1024


def extract_csrf_token(html_content: str) -> str | None:
    """Token CSRF del formulario de baja. None si no está (señal de sesión vencida
    o de que el formulario no está disponible por otro motivo — ver delete_device)."""
    m = _CSRF_TOKEN_RE.search(html_content)
    return m.group(1) if m else None


def is_delete_success(response_body: str) -> bool:
    return DELETE_SUCCESS_MARKER in response_body
