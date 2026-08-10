from collections.abc import Awaitable, Callable
from typing import TypeVar

from src.modules.insumos.domain.errors import OrderAlreadyInProgressError
from src.modules.insumos.domain.repositories.order_claim_repository import (
    OrderClaimRepository,
)

T = TypeVar("T")


class ClaimedOrderCreation:
    """Reemplaza la garantía que daba `KeyedLock.acquire((serial, sku))` en
    la app legacy: serializa quién puede procesar una serie+sku a la vez,
    para que dos intentos concurrentes (un click manual y el poller, o dos
    clicks) no pasen ambos el chequeo anti-duplicados antes de que el
    primero registre el pedido.

    A diferencia del lock en memoria, esto no mantiene ninguna transacción
    de Postgres abierta durante la I/O externa larga (la llamada SOAP real
    más sus reintentos de verificación pueden tardar varios segundos) — se
    reclama la clave, se ejecuta `action` fuera de cualquier lock de DB, y
    se libera al terminar, haya salido bien o mal.
    """

    def __init__(self, claims: OrderClaimRepository) -> None:
        self._claims = claims

    async def run(
        self, *, device_serial: str, sku: str, action: Callable[[], Awaitable[T]]
    ) -> T:
        if not await self._claims.try_claim(device_serial, sku):
            raise OrderAlreadyInProgressError(device_serial, sku)
        try:
            return await action()
        finally:
            await self._claims.release(device_serial, sku)
