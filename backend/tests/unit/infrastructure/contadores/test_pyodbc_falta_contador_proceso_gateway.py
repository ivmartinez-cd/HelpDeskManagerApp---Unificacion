"""PyodbcFaltaContadorProcesoGateway con un runner fake: parámetros exactos
de las dos consultas, mapeo Mono/Color, y ProcesoNoEncontradoError cuando el
proceso no tiene ninguna fila en Factura_Contador."""

from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any

import pytest

from src.modules.contadores.domain.errors import ProcesoNoEncontradoError
from src.modules.contadores.infrastructure.siges.falta_contador_proceso_query import (
    CLIENTE_POR_PROCESO_SQL,
    FALTA_CONTADOR_POR_PROCESO_SQL,
)
from src.modules.contadores.infrastructure.siges.pyodbc_falta_contador_proceso_gateway import (
    PyodbcFaltaContadorProcesoGateway,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class FakeRunner:
    """Imita `MercurioQueryRunner.fetch_all` registrando cada llamada."""

    def __init__(self, filas_por_sql: dict[str, list[Any]] | None = None) -> None:
        self.filas_por_sql = filas_por_sql or {}
        self.llamadas: list[tuple[str, tuple[object, ...], str]] = []

    async def fetch_all(
        self, sql: str, params: Sequence[object] = (), *, gateway: str, **_: Any
    ) -> list[Any]:
        self.llamadas.append((sql, tuple(params), gateway))
        return list(self.filas_por_sql.get(sql, []))


async def test_fetch_mapea_mono_y_color_y_consulta_cliente_y_filas() -> None:
    runner = FakeRunner(
        {
            CLIENTE_POR_PROCESO_SQL: [SimpleNamespace(cliente="Cepas Argentina ")],
            FALTA_CONTADOR_POR_PROCESO_SQL: [
                SimpleNamespace(serie="ABC123", clase=10, contador=100),
                SimpleNamespace(serie="ABC123", clase=20, contador=50),
            ],
        }
    )
    gateway = PyodbcFaltaContadorProcesoGateway(runner)  # type: ignore[arg-type]

    resultado = await gateway.fetch(99070)

    assert resultado.cliente == "Cepas Argentina"
    assert [f.nombre_clase for f in resultado.filas] == ["Mono", "Color"]
    assert all(f.tipo == "FALTA CONTADOR" for f in resultado.filas)
    assert [f.contador for f in resultado.filas] == [100, 50]
    assert runner.llamadas == [
        (CLIENTE_POR_PROCESO_SQL, (99070,), "falta_contador_proceso_cliente"),
        (FALTA_CONTADOR_POR_PROCESO_SQL, (99070,), "falta_contador_proceso"),
    ]


async def test_fetch_sin_filas_de_cliente_levanta_proceso_no_encontrado() -> None:
    runner = FakeRunner({CLIENTE_POR_PROCESO_SQL: []})
    gateway = PyodbcFaltaContadorProcesoGateway(runner)  # type: ignore[arg-type]

    with pytest.raises(ProcesoNoEncontradoError):
        await gateway.fetch(1)

    # No consulta las filas si el proceso ni existe.
    assert [sql for sql, _, _ in runner.llamadas] == [CLIENTE_POR_PROCESO_SQL]


async def test_fetch_sin_filas_falta_contador_devuelve_lista_vacia() -> None:
    runner = FakeRunner({CLIENTE_POR_PROCESO_SQL: [SimpleNamespace(cliente="Cliente SA")]})
    gateway = PyodbcFaltaContadorProcesoGateway(runner)  # type: ignore[arg-type]

    resultado = await gateway.fetch(5)

    assert resultado.cliente == "Cliente SA"
    assert resultado.filas == []


async def test_error_de_pyodbc_se_envuelve_en_external_service_error() -> None:
    runner = MercurioQueryRunner(
        "DRIVER={Driver Inexistente};SERVER=nohost;DATABASE=Siges;UID=x;PWD=x",
        timeout_seconds=1.0,
    )
    gateway = PyodbcFaltaContadorProcesoGateway(runner)
    with pytest.raises(ExternalServiceError):
        await gateway.fetch(1)
