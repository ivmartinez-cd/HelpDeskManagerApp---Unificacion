"""PyodbcDetalleContadorProcesoGateway con un runner fake: una sola consulta
(cliente derivado de la primera fila), mapeo Mono/Color, `contador_actual`
en 0 cuando falta el contador (no repite el valor viejo, ver docstring de la
query), `tipo` combinando "FALTA CONTADOR"/"AUTOMATICO"/`None`, y
ProcesoNoEncontradoError cuando el proceso no tiene ninguna fila."""

from collections.abc import Sequence
from datetime import datetime
from types import SimpleNamespace
from typing import Any

import pytest

from src.modules.contadores.domain.errors import ProcesoNoEncontradoError
from src.modules.contadores.infrastructure.siges.detalle_contador_proceso_query import (
    DETALLE_CONTADORES_POR_PROCESO_SQL,
)
from src.modules.contadores.infrastructure.siges.pyodbc_detalle_contador_proceso_gateway import (
    PyodbcDetalleContadorProcesoGateway,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.orion.query_runner import OrionQueryRunner


class FakeRunner:
    """Imita `OrionQueryRunner.fetch_all` registrando cada llamada."""

    def __init__(self, filas_por_sql: dict[str, list[Any]] | None = None) -> None:
        self.filas_por_sql = filas_por_sql or {}
        self.llamadas: list[tuple[str, tuple[object, ...], str]] = []

    async def fetch_all(
        self, sql: str, params: Sequence[object] = (), *, gateway: str, **_: Any
    ) -> list[Any]:
        self.llamadas.append((sql, tuple(params), gateway))
        return list(self.filas_por_sql.get(sql, []))


def _fila(**overrides: Any) -> SimpleNamespace:
    base = dict(
        empresa="ISSN ",
        sucursal="Botiquin Caviahue",
        sector="Indeterminado",
        modelo="MFP Mono HP 432fdn",
        serie="CNB1R4C0MV",
        clase=10,
        fecha_toma_anterior=datetime(2026, 8, 18),
        contador_anterior=1,
        fecha_toma_actual=datetime(2026, 8, 18),
        contador_actual_bruto=1,
        impresiones_reales=0.0,
        estado_maquina="Activa en Cliente",
        direccion_ip=" ",
        mascara_ip=" ",
        falta_contador=1,
        es_automatico=0,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


async def test_fetch_falta_contador_muestra_contador_actual_en_cero_y_tipo() -> None:
    runner = FakeRunner({DETALLE_CONTADORES_POR_PROCESO_SQL: [_fila()]})
    gateway = PyodbcDetalleContadorProcesoGateway(runner)  # type: ignore[arg-type]

    resultado = await gateway.fetch(99089)

    assert resultado.cliente == "ISSN"
    fila = resultado.filas[0]
    assert fila.empresa == "ISSN"
    assert fila.sucursal == "Botiquin Caviahue"
    assert fila.modelo == "MFP Mono HP 432fdn"
    assert fila.nombre_clase == "Mono"
    assert fila.contador_anterior == 1
    # Verificado contra la captura real: aunque ImpreContadorActual=1 (mismo
    # registro físico que el anterior), el reporte muestra 0.
    assert fila.contador_actual == 0
    assert fila.direccion_ip is None
    assert fila.mascara_ip is None
    assert fila.falta_contador is True
    assert fila.tipo == "FALTA CONTADOR Mono"
    assert runner.llamadas == [
        (DETALLE_CONTADORES_POR_PROCESO_SQL, (99089,), "detalle_contador_proceso"),
    ]


async def test_fetch_lectura_real_respeta_contador_actual_bruto() -> None:
    fila_real = _fila(
        contador_anterior=417,
        contador_actual_bruto=497,
        impresiones_reales=80.0,
        falta_contador=0,
        es_automatico=0,
    )
    runner = FakeRunner({DETALLE_CONTADORES_POR_PROCESO_SQL: [fila_real]})
    gateway = PyodbcDetalleContadorProcesoGateway(runner)  # type: ignore[arg-type]

    resultado = await gateway.fetch(99089)

    fila = resultado.filas[0]
    assert fila.contador_actual == 497
    assert fila.falta_contador is False
    assert fila.tipo is None


async def test_fetch_automatico_no_repite_falta_contador() -> None:
    fila_auto = _fila(falta_contador=0, es_automatico=1, impresiones_reales=0.0)
    runner = FakeRunner({DETALLE_CONTADORES_POR_PROCESO_SQL: [fila_auto]})
    gateway = PyodbcDetalleContadorProcesoGateway(runner)  # type: ignore[arg-type]

    resultado = await gateway.fetch(99089)

    fila = resultado.filas[0]
    assert fila.falta_contador is False
    assert fila.tipo == "AUTOMATICO"
    assert fila.contador_actual == 1


async def test_fetch_sin_filas_levanta_proceso_no_encontrado() -> None:
    runner = FakeRunner({})
    gateway = PyodbcDetalleContadorProcesoGateway(runner)  # type: ignore[arg-type]

    with pytest.raises(ProcesoNoEncontradoError):
        await gateway.fetch(1)


async def test_error_de_pyodbc_se_envuelve_en_external_service_error() -> None:
    runner = OrionQueryRunner(
        "DRIVER={Driver Inexistente};SERVER=nohost;DATABASE=Siges;UID=x;PWD=x",
        timeout_seconds=1.0,
    )
    gateway = PyodbcDetalleContadorProcesoGateway(runner)
    with pytest.raises(ExternalServiceError):
        await gateway.fetch(1)
