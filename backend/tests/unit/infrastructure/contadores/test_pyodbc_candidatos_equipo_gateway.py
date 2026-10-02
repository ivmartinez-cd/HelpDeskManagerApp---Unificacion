"""PyodbcCandidatosEquipoGateway con un runner fake — replica
`SiGesRepository.GetCandidatosAsync` + `GetCandidatos.sql` del legacy:
`Para_Facturar` del tipo de toma, snapshot de ubicación y marcas de cambio
de empresa/sucursal/anexo (excluyentes) entre lecturas vecinas."""

from collections.abc import Sequence
from datetime import date, datetime
from typing import Any

from src.modules.contadores.infrastructure.siges.candidatos_query import (
    CANDIDATOS_EQUIPO_SQL,
    CANDIDATOS_EQUIPOS_LOTE_SQL,
)
from src.modules.contadores.infrastructure.siges.pyodbc_candidatos_equipo_gateway import (
    PyodbcCandidatosEquipoGateway,
)


class FakeRunner:
    def __init__(self, filas: list[tuple[Any, ...]]) -> None:
        self.filas = filas
        self.llamadas: list[tuple[str, tuple[object, ...]]] = []

    async def fetch_all(self, sql: str, params: Sequence[object] = (), **_: Any) -> list[Any]:
        self.llamadas.append((sql, tuple(params)))
        return list(self.filas)


def _fila(
    id_contador: int, dia: int, ubicacion: tuple[int | None, int | None, int | None] = (1, 1, 1),
    tipo: int = 1, para_facturar: bool | None = True,
) -> tuple[Any, ...]:
    empresa, sucursal, anexo = ubicacion
    return (
        id_contador, 77, 10, datetime(2026, 4, dia), 1000.0 + dia, tipo, f"Tipo {tipo}",
        para_facturar, empresa, sucursal, anexo,
    )


async def _lecturas(*filas: tuple[Any, ...]) -> Any:
    gateway = PyodbcCandidatosEquipoGateway(FakeRunner(list(filas)))  # type: ignore[arg-type]
    return await gateway.fetch_lecturas(77, 10)


def test_sql_une_tipo_toma_y_trae_snapshot_de_ubicacion_como_el_legacy() -> None:
    sql = " ".join(CANDIDATOS_EQUIPO_SQL.split())

    assert "INNER JOIN Tipo_Toma TT WITH (NOLOCK) ON TT.id = C.ID_TipoToma" in sql
    assert "TT.Para_Facturar" in sql and "C.Para_Facturar" not in sql
    assert "C.ID_Empresa, C.ID_Sucursal, C.ID_Anexo" in sql
    assert "ORDER BY C.FechaTomaContador DESC, C.ID_Contador DESC" in sql


async def test_mapea_columnas_en_orden_y_consulta_por_maquina_y_clase() -> None:
    runner = FakeRunner([_fila(501, 20, (3, 4, 5), tipo=4, para_facturar=False)])
    gateway = PyodbcCandidatosEquipoGateway(runner)  # type: ignore[arg-type]

    lectura = (await gateway.fetch_lecturas(77, 10))[0]

    assert runner.llamadas == [(CANDIDATOS_EQUIPO_SQL, (77, 10))]
    assert lectura.id_contador == 501
    assert lectura.fecha == date(2026, 4, 20)
    assert lectura.valor == 1020.0
    assert (lectura.tipo_toma, lectura.desc_tipo_toma) == (4, "Tipo 4")
    assert lectura.para_facturar is False
    assert (lectura.id_empresa, lectura.id_sucursal, lectura.id_anexo) == (3, 4, 5)


async def test_para_facturar_null_se_lee_como_false() -> None:
    lectura = (await _lecturas(_fila(1, 20, para_facturar=None)))[0]

    assert lectura.para_facturar is False


async def test_cambio_de_empresa_tapa_sucursal_y_anexo() -> None:
    reciente, vieja = await _lecturas(_fila(2, 20, (2, 9, 9)), _fila(1, 10, (1, 1, 1)))

    assert reciente.cambio_empresa_vs_anterior is True
    assert reciente.cambio_sucursal_vs_anterior is False
    assert reciente.cambio_anexo_vs_anterior is False
    assert not (vieja.cambio_empresa_vs_anterior or vieja.cambio_sucursal_vs_anterior)


async def test_cambio_de_sucursal_tapa_anexo() -> None:
    reciente, _ = await _lecturas(_fila(2, 20, (1, 2, 9)), _fila(1, 10, (1, 1, 1)))

    assert (reciente.cambio_sucursal_vs_anterior, reciente.cambio_anexo_vs_anterior) == (
        True, False
    )


async def test_cambio_de_anexo_solo() -> None:
    reciente, _ = await _lecturas(_fila(2, 20, (1, 1, 2)), _fila(1, 10, (1, 1, 1)))

    assert reciente.cambio_anexo_vs_anterior is True
    assert not reciente.cambio_empresa_vs_anterior


async def test_snapshot_null_no_marca_cambio() -> None:
    reciente, _ = await _lecturas(_fila(2, 20, (None, 2, 1)), _fila(1, 10, (1, 1, 1)))

    assert reciente.cambio_empresa_vs_anterior is False
    assert reciente.cambio_sucursal_vs_anterior is True


async def test_sin_lecturas_devuelve_lista_vacia() -> None:
    assert await _lecturas() == []


async def test_lote_una_sola_consulta_y_agrupa_por_equipo_y_clase() -> None:
    otra_clase = (*_fila(3, 5)[:2], 20, *_fila(3, 5)[3:])
    runner = FakeRunner([_fila(2, 20), _fila(1, 10), otra_clase])
    gateway = PyodbcCandidatosEquipoGateway(runner)  # type: ignore[arg-type]

    lote = await gateway.fetch_lecturas_de_equipos([(77, 10), (88, 10)])

    assert runner.llamadas == [(CANDIDATOS_EQUIPOS_LOTE_SQL.format(maquinas="?, ?"), (77, 88))]
    assert [lectura.id_contador for lectura in lote[(77, 10)]] == [2, 1]
    assert (77, 20) not in lote and (88, 10) not in lote
    assert await gateway.fetch_lecturas_de_equipos([]) == {}
