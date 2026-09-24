"""PyodbcProcesoEstimacionGateway: el combo de procesos entrega
`PeriodoHasta` como `date` (`DateOnly.FromDateTime` del legacy), aunque
pyodbc/FreeTDS lo devuelva como `datetime` — es la fecha objetivo por
defecto del tablero."""

from collections.abc import Sequence
from datetime import date, datetime
from types import SimpleNamespace
from typing import Any

from src.modules.contadores.infrastructure.siges.pyodbc_proceso_estimacion_gateway import (
    PyodbcProcesoEstimacionGateway,
)


class FakeRunner:
    def __init__(self, filas: list[Any]) -> None:
        self.filas = filas
        self.params: tuple[object, ...] = ()

    async def fetch_all(self, sql: str, params: Sequence[object] = (), **_: Any) -> list[Any]:
        self.params = tuple(params)
        return self.filas


async def test_periodo_hasta_datetime_se_entrega_como_date() -> None:
    fila = SimpleNamespace(
        Nro_Proceso=321, PeriodoFacturacion="2026-04", NombreAnexo="Anexo A",
        PeriodoHasta=datetime(2026, 4, 30), ID_Anexo=44,
    )
    runner = FakeRunner([fila])

    procesos = await PyodbcProcesoEstimacionGateway(runner).list_procesos_por_grupo(900)  # type: ignore[arg-type]

    assert runner.params == (900,)
    assert procesos[0].periodo_hasta == date(2026, 4, 30)
    assert type(procesos[0].periodo_hasta) is date
    assert (procesos[0].nro_proceso, procesos[0].id_anexo) == (321, 44)
