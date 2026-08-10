import asyncio
from collections.abc import Awaitable, Callable, Sequence

# Backoff fijo replicado de la app legacy (canal_directo_soap_client.py,
# _VERIFY_RETRY_DELAYS_SECONDS) — no es un valor arbitrario: nace de un
# incidente real (pedido 443017 / SDS-974325, 2026-08-03) donde la primera
# lectura post-creación no vio el pedido recién creado por lag de Canal
# Directo, y recién se confirmó unos segundos después.
DEFAULT_RETRY_DELAYS_SECONDS: tuple[float, ...] = (0, 1, 2, 4)


async def verify_with_retries(
    check: Callable[[], Awaitable[bool]],
    delays: Sequence[float] = DEFAULT_RETRY_DELAYS_SECONDS,
) -> bool:
    """Reintenta `check` con el backoff dado hasta que devuelva True o se
    agoten los reintentos. `check` encapsula la relectura + comparación
    real (en el paso siguiente: `getSupplyById` comparando
    `NroIncidenteCliente` contra la referencia esperada) — acá no se sabe
    nada de SOAP, solo el patrón de reintento."""
    for delay in delays:
        if delay:
            await asyncio.sleep(delay)
        if await check():
            return True
    return False
