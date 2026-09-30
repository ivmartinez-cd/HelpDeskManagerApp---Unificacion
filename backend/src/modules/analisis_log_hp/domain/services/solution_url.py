"""Hosts de HP de los que el backend acepta bajar el contenido de una solución.
El link lo carga un usuario y el backend lo pide con su propia red: sin esta lista
servía para leer servicios internos (DB, backend, Mailpit) — auditoría de
seguridad 2026-09-30. Las URLs cargadas hoy son todas del content bootstrapper."""

from urllib.parse import urlsplit

HOSTS_PERMITIDOS = frozenset(
    {"api-sds-contentbootstrapper-prod.sds.hp8.us", "hp-sds-latam.insightportal.net"}
)


def es_solution_url_permitida(url: str) -> bool:
    partes = urlsplit(url.strip())
    return partes.scheme == "https" and (partes.hostname or "") in HOSTS_PERMITIDOS
