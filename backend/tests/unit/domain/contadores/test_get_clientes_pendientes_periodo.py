from datetime import UTC, datetime

import pytest

from src.modules.contadores.application.use_cases.get_clientes_pendientes_periodo import (
    GetClientesPendientesPeriodo,
)
from src.modules.contadores.domain.entities.clientes_pendientes_periodo import (
    ClientesPendientesPeriodo,
)
from src.shared.domain.errors import ExternalServiceError

_CONSULTADO_EN = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)


class _FakePort:
    def __init__(
        self, resultado: ClientesPendientesPeriodo | None = None, *, falla: bool = False
    ) -> None:
        self._resultado = resultado
        self._falla = falla

    async def contar(self, *, force_refresh: bool = False) -> ClientesPendientesPeriodo:
        if self._falla:
            raise ExternalServiceError("Siges caído")
        assert self._resultado is not None
        return self._resultado


@pytest.mark.asyncio
async def test_devuelve_el_resultado_del_puerto() -> None:
    resultado = ClientesPendientesPeriodo(
        periodo="202607",
        grupos=("Cliente A", "Cliente B"),
        consultado_en=_CONSULTADO_EN,
    )
    port = _FakePort(resultado)
    assert await GetClientesPendientesPeriodo(port).execute() == resultado


def test_cantidad_es_la_cantidad_de_grupos() -> None:
    resultado = ClientesPendientesPeriodo(
        periodo="202607",
        grupos=("Cliente A", "Cliente B", "Cliente C"),
        consultado_en=_CONSULTADO_EN,
    )
    assert resultado.cantidad == 3


@pytest.mark.asyncio
async def test_siges_caido_devuelve_none_sin_inventar_un_cero() -> None:
    port = _FakePort(falla=True)
    assert await GetClientesPendientesPeriodo(port).execute() is None
