import logging
from datetime import date

import httpx

from src.modules.vacaciones.domain.repositories.feriados_externos import FeriadoImportado
from src.shared.domain.errors import ExternalServiceError

_logger = logging.getLogger(__name__)

_BASE_URL = "https://api.argentinadatos.com/v1/feriados"
_TIMEOUT_SECONDS = 15.0


class ArgentinaDatosFeriadosClient:
    """Feriados de Argentina desde api.argentinadatos.com (misma fuente que el
    import del legacy). Respuesta: [{"fecha": "YYYY-MM-DD", "tipo": ...,
    "nombre": ...}]."""

    async def fetch(self, year: int) -> list[FeriadoImportado]:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                response = await client.get(f"{_BASE_URL}/{year}")
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            _logger.error(
                "Fallo consultando feriados en argentinadatos",
                extra={"year": year},
                exc_info=exc,
            )
            raise ExternalServiceError(
                f"No se pudieron obtener los feriados {year} de argentinadatos"
            ) from exc
        return _parse(payload)


def _parse(payload: object) -> list[FeriadoImportado]:
    if not isinstance(payload, list):
        raise ExternalServiceError("Respuesta inesperada de argentinadatos (no es una lista)")
    feriados: list[FeriadoImportado] = []
    for item in payload:
        try:
            feriados.append(
                FeriadoImportado(
                    fecha=date.fromisoformat(item["fecha"]), nombre=str(item["nombre"])
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            _logger.warning(
                "Feriado inválido en la respuesta de argentinadatos, se ignora",
                extra={"item": item},
                exc_info=exc,
            )
    return feriados
