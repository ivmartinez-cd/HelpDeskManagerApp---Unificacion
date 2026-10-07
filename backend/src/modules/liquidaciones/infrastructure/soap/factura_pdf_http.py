"""¿Existe el PDF de factura en webagentes? — HEAD contra la URL reconstruida
(`domain/services/factura_pdf_url.py`). AyC informa el número de factura aunque
el archivo no esté (caso 3988-0, 2026-10-07: número 1-78 en AyC, PDF en 404),
así que el número solo no alcanza para decir que el prestador la cargó."""

import logging

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 10.0


async def head_pdf_existe(url: str) -> bool:
    """False también si la consulta falla (se loguea): la reconciliación
    reintenta en la próxima corrida."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            resp = await client.head(url)
    except httpx.HTTPError as exc:
        logger.warning("HEAD al PDF de factura falló", extra={"url": url}, exc_info=exc)
        return False
    return resp.status_code == 200
