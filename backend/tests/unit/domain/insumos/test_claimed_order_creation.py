"""Tests unitarios de ClaimedOrderCreation — el reemplazo de KeyedLock.

Usa un fake de OrderClaimRepository en memoria: la garantía real de
concurrencia (dos procesos compitiendo de verdad) se prueba contra Postgres
en tests/integration/infrastructure/insumos/test_sqlalchemy_order_claim_repository.py.
"""
import pytest

from src.modules.insumos.domain.errors import OrderAlreadyInProgressError
from src.modules.insumos.domain.services.claimed_order_creation import ClaimedOrderCreation


class FakeOrderClaimRepository:
    def __init__(self) -> None:
        self._claimed: set[tuple[str, str]] = set()
        self.released: list[tuple[str, str]] = []

    async def try_claim(self, device_serial: str, sku: str) -> bool:
        key = (device_serial, sku)
        if key in self._claimed:
            return False
        self._claimed.add(key)
        return True

    async def release(self, device_serial: str, sku: str) -> None:
        self._claimed.discard((device_serial, sku))
        self.released.append((device_serial, sku))


async def test_run_executes_action_and_releases_the_claim_on_success() -> None:
    claims = FakeOrderClaimRepository()
    service = ClaimedOrderCreation(claims)

    async def action() -> str:
        return "order-created"

    result = await service.run(device_serial="SER1", sku="SKU1", action=action)

    assert result == "order-created"
    assert claims.released == [("SER1", "SKU1")]
    assert ("SER1", "SKU1") not in claims._claimed


async def test_run_releases_the_claim_even_if_action_raises() -> None:
    claims = FakeOrderClaimRepository()
    service = ClaimedOrderCreation(claims)

    async def action() -> None:
        raise RuntimeError("La llamada SOAP falló")

    with pytest.raises(RuntimeError):
        await service.run(device_serial="SER1", sku="SKU1", action=action)

    assert claims.released == [("SER1", "SKU1")]


async def test_run_raises_order_already_in_progress_when_claim_is_taken() -> None:
    claims = FakeOrderClaimRepository()
    service = ClaimedOrderCreation(claims)
    await claims.try_claim("SER1", "SKU1")  # simula otro proceso con el claim activo

    async def action() -> None:
        pytest.fail("no debería ejecutarse si el claim ya está tomado")

    with pytest.raises(OrderAlreadyInProgressError):
        await service.run(device_serial="SER1", sku="SKU1", action=action)

    assert claims.released == []  # nunca se reclamó, no hay nada que liberar
