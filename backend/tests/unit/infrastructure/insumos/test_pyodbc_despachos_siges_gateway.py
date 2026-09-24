"""PyodbcDespachosSigesGateway con un runner falso en memoria: SQL y orden de parámetros,
nombre del gateway en el log, entradas que no consultan y errores del runner que se
propagan (sin red ni driver real)."""

from collections.abc import Sequence
from datetime import datetime
from types import SimpleNamespace
from typing import Any

import pytest

from src.modules.insumos.infrastructure.siges.consulta_despachos import (
    construir_consulta_despachos,
)
from src.modules.insumos.infrastructure.siges.pyodbc_despachos_siges_gateway import (
    PyodbcDespachosSigesGateway,
)
from src.shared.domain.errors import ExternalServiceError


class RunnerFalso:
    """Imita `OrionQueryRunner.fetch_all` registrando cada llamada."""

    def __init__(self, filas: list[Any] | None = None, error: Exception | None = None) -> None:
        self.filas = filas or []
        self.error = error
        self.llamadas: list[tuple[str, tuple[object, ...], dict[str, Any]]] = []

    async def fetch_all(self, sql: str, params: Sequence[object] = (), **kwargs: Any) -> list[Any]:
        self.llamadas.append((sql, tuple(params), kwargs))
        if self.error is not None:
            raise self.error
        return list(self.filas)


def _gateway(runner: RunnerFalso) -> PyodbcDespachosSigesGateway:
    # El gateway solo usa `fetch_all` del runner; el falso cumple ese contrato.
    return PyodbcDespachosSigesGateway(runner)  # type: ignore[arg-type]


def _fila() -> SimpleNamespace:
    return SimpleNamespace(
        id_remito=10,
        numero_remito=5500,
        guia="3867500000001234567",
        id_distribucion=9,
        fecha_remito=datetime(2026, 9, 22),
        bultos=1,
        entrega_a="",
        cliente="Cliente SA",
        sucursal_cliente="Casa Central",
        numero_incidente="446207",
        numero_incidente_cliente="",
    )


async def test_consulta_con_las_distribuciones_primero_y_la_ventana_al_final() -> None:
    runner = RunnerFalso([_fila()])

    despachos = await _gateway(runner).listar_despachos_oca(
        dias_ventana=30, distribuciones=(3, 9, 10)
    )

    [(sql, params, kwargs)] = runner.llamadas
    assert sql == construir_consulta_despachos(3)
    assert params == (3, 9, 10, 30)
    assert kwargs["gateway"] == "insumos_despachados_siges"
    assert [d.guia for d in despachos] == ["3867500000001234567"]


async def test_el_log_de_error_lleva_la_ventana_y_las_distribuciones_en_el_mensaje() -> None:
    runner = RunnerFalso()

    await _gateway(runner).listar_despachos_oca(dias_ventana=15, distribuciones=(3,))

    [(_, _, kwargs)] = runner.llamadas
    assert kwargs["log_message"].startswith("Falló la consulta de despachos OCA")
    assert "dias_ventana=15" in kwargs["log_message"]
    assert "distribuciones=[3]" in kwargs["log_message"]


async def test_sin_distribuciones_no_consulta() -> None:
    runner = RunnerFalso([_fila()])

    despachos = await _gateway(runner).listar_despachos_oca(dias_ventana=30, distribuciones=())

    assert despachos == []
    assert runner.llamadas == []


@pytest.mark.parametrize("dias_ventana", [0, -5])
async def test_ventana_menor_a_un_dia_es_un_error_y_no_consulta(dias_ventana: int) -> None:
    runner = RunnerFalso()

    with pytest.raises(ValueError):
        await _gateway(runner).listar_despachos_oca(dias_ventana=dias_ventana, distribuciones=(3,))

    assert runner.llamadas == []


async def test_el_error_externo_del_runner_se_propaga() -> None:
    runner = RunnerFalso(error=ExternalServiceError("No se pudo consultar la base Siges (ORION)"))

    with pytest.raises(ExternalServiceError):
        await _gateway(runner).listar_despachos_oca(dias_ventana=30, distribuciones=(3,))
