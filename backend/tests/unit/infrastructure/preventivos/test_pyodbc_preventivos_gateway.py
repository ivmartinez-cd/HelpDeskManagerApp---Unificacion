"""PyodbcPreventivosGateway con un runner fake en memoria: parámetros de la
consulta, caché TTL por zona, force_refresh, catálogo de zonas y el envoltorio
de errores del runner compartido (sin red ni driver real)."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest

from src.modules.preventivos.infrastructure.siges.pyodbc_preventivos_gateway import (
    PyodbcPreventivosGateway,
)
from src.modules.preventivos.infrastructure.siges.query import PARQUE_ZONA_SQL, ZONAS_SQL
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


def _fila_equipo(id_maquina: int, zona: str = "SUR") -> SimpleNamespace:
    return SimpleNamespace(
        id_maquina=id_maquina,
        id_sucursal=id_maquina,
        serie=f"S{id_maquina}",
        modelo="MFP Mono Samsung",
        cliente="Cliente SA",
        sucursal="Casa Central",
        zona=zona,
        frecuencia_dias=180,
        fecha_ultimo_preventivo=None,
        fecha_instalacion=None,
        domicilio="Calle Falsa 123",
        latitud="-34.6",
        longitud="-58.4",
    )


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


def _gateway(
    runner: FakeRunner,
    ttl: float = 300.0,
    meses: int = 3,
    zonas_ttl: float | None = None,
) -> PyodbcPreventivosGateway:
    # El gateway solo usa `fetch_all` del runner; el fake cumple ese contrato.
    return PyodbcPreventivosGateway(
        runner,  # type: ignore[arg-type]
        cache_ttl_seconds=ttl,
        meses_actividad=meses,
        zonas_cache_ttl_seconds=zonas_ttl,
    )


async def test_consulta_el_parque_con_meses_de_actividad_y_zona() -> None:
    runner = FakeRunner({PARQUE_ZONA_SQL: [_fila_equipo(1), _fila_equipo(2)]})

    snapshot = await _gateway(runner, meses=4).list_equipos_por_zona("SUR")

    assert runner.llamadas == [(PARQUE_ZONA_SQL, (4, 4, "SUR"), "preventivos_parque_zona")]
    assert [e.id_maquina for e in snapshot.equipos] == [1, 2]
    assert snapshot.consultado_en.tzinfo is UTC


async def test_segunda_lectura_de_la_misma_zona_sale_de_cache() -> None:
    runner = FakeRunner({PARQUE_ZONA_SQL: [_fila_equipo(1)]})
    gateway = _gateway(runner)

    primero = await gateway.list_equipos_por_zona("SUR")
    segundo = await gateway.list_equipos_por_zona("SUR")

    assert segundo is primero
    assert len(runner.llamadas) == 1


async def test_zonas_distintas_tienen_cache_independiente() -> None:
    runner = FakeRunner()
    gateway = _gateway(runner)

    await gateway.list_equipos_por_zona("SUR")
    await gateway.list_equipos_por_zona("NORTE")

    assert [params[2] for _, params, _ in runner.llamadas] == ["SUR", "NORTE"]


async def test_force_refresh_vuelve_a_consultar_aunque_la_cache_este_vigente() -> None:
    runner = FakeRunner()
    gateway = _gateway(runner)

    primero = await gateway.list_equipos_por_zona("SUR")
    segundo = await gateway.list_equipos_por_zona("SUR", force_refresh=True)

    assert segundo is not primero
    assert len(runner.llamadas) == 2


async def test_cache_vencida_vuelve_a_consultar() -> None:
    runner = FakeRunner()
    gateway = _gateway(runner, ttl=0.0)

    await gateway.list_equipos_por_zona("SUR")
    await gateway.list_equipos_por_zona("SUR")

    assert len(runner.llamadas) == 2


async def test_list_zonas_consulta_el_catalogo_y_lo_cachea() -> None:
    filas = [SimpleNamespace(zona="SUR", maquinas_activas=3)]
    runner = FakeRunner({ZONAS_SQL: filas})
    gateway = _gateway(runner, meses=5)

    primero = await gateway.list_zonas()
    segundo = await gateway.list_zonas()

    assert runner.llamadas == [(ZONAS_SQL, (5, 5), "preventivos_zonas")]
    assert [(z.zona, z.maquinas_activas) for z in primero] == [("SUR", 3)]
    assert segundo is primero


async def test_list_zonas_usa_su_propio_ttl_mas_largo_que_el_de_equipos() -> None:
    # TTL de equipos vencido (0.0) no debería afectar la caché de zonas.
    runner = FakeRunner()
    gateway = _gateway(runner, ttl=0.0, zonas_ttl=1800.0)

    await gateway.list_zonas()
    await gateway.list_zonas()

    assert len(runner.llamadas) == 1


async def test_list_zonas_vencido_vuelve_a_consultar() -> None:
    runner = FakeRunner()
    gateway = _gateway(runner, ttl=0.0)

    await gateway.list_zonas()
    await gateway.list_zonas()

    assert len(runner.llamadas) == 2


def test_es_vigente_respeta_el_ttl() -> None:
    gateway = _gateway(FakeRunner(), ttl=60.0)
    ahora = datetime.now(UTC)

    assert gateway._es_vigente(None) is False
    assert gateway._es_vigente(ahora) is True
    assert gateway._es_vigente(ahora - timedelta(seconds=61)) is False


async def test_error_de_pyodbc_se_envuelve_en_external_service_error() -> None:
    """Un driver inexistente hace fallar el connect al instante (sin red); lo
    que importa es que al caller nunca le llegue la excepción cruda (§6)."""
    runner = MercurioQueryRunner(
        "DRIVER={Driver Inexistente};SERVER=nohost;DATABASE=Siges;UID=x;PWD=x",
        timeout_seconds=1.0,
    )
    gateway = PyodbcPreventivosGateway(runner, cache_ttl_seconds=60.0, meses_actividad=3)

    with pytest.raises(ExternalServiceError):
        await gateway.list_equipos_por_zona("SUR")
