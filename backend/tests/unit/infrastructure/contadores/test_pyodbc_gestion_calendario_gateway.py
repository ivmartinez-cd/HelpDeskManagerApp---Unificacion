"""PyodbcGestionCalendarioGateway con un runner fake: arma los eventos con el
mismo formato que devolvía la web de Gestión (ADR-047)."""

from collections.abc import Sequence
from datetime import date, datetime
from types import SimpleNamespace
from typing import Any

from src.modules.contadores.infrastructure.siges.gestion_calendario_query import (
    GESTION_CALENDARIO_FACTURACION_SQL,
)
from src.modules.contadores.infrastructure.siges.pyodbc_gestion_calendario_gateway import (
    PyodbcGestionCalendarioGateway,
)


class FakeRunner:
    def __init__(self, filas: list[Any]) -> None:
        self.filas = filas
        self.llamadas: list[tuple[str, tuple[object, ...]]] = []

    async def fetch_all(self, sql: str, params: Sequence[object] = (), **_: Any) -> list[Any]:
        self.llamadas.append((sql, tuple(params)))
        return list(self.filas)


def _fila(**overrides: object) -> SimpleNamespace:
    base: dict[str, object] = {
        "id": 25525,
        "fecha": datetime(2026, 10, 9),
        "titulo": "AGS Comercializadora",
        "descripcion": "Pedir archivo por mail",
        "username": "ltorres",
        "color": "#FFC0CB",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


async def test_arma_el_evento_como_lo_mandaba_la_web() -> None:
    runner = FakeRunner([_fila()])

    [evento] = await PyodbcGestionCalendarioGateway(runner).get_events(  # type: ignore[arg-type]
        "2026-07-11", "2027-01-07"
    )

    assert evento.id == "25525"
    assert evento.title == "(Facturación) AGS Comercializadora"
    assert evento.cliente == evento.tittle_tooltip == "AGS Comercializadora"
    assert evento.start == "2026-10-09T00:00:00-03:00"
    assert evento.operador_id == "ltorres"
    assert evento.background_color == evento.border_color == "#FFC0CB"
    assert (evento.type, evento.string_tipo_evento, evento.all_day) == ("E", "Facturación", True)
    assert evento.content_tooltip == "Pedir archivo por mail"
    assert evento.vendedor is None and evento.sucursal_entrega is None


async def test_operador_sin_color_usa_el_amarillo_de_la_web() -> None:
    runner = FakeRunner([_fila(username="vipaez", color=None)])

    [evento] = await PyodbcGestionCalendarioGateway(runner).get_events(  # type: ignore[arg-type]
        "2026-10-01", "2026-10-31"
    )

    assert evento.background_color == evento.border_color == "#FACC2E"


async def test_el_fin_del_rango_es_inclusivo() -> None:
    runner = FakeRunner([])

    await PyodbcGestionCalendarioGateway(runner).get_events(  # type: ignore[arg-type]
        "2026-10-01", "2026-10-31"
    )

    assert runner.llamadas == [
        (GESTION_CALENDARIO_FACTURACION_SQL, (date(2026, 10, 1), date(2026, 11, 1)))
    ]


def test_sql_agrupa_por_padre_y_fecha_y_oculta_el_grupo_realizado() -> None:
    sql = " ".join(GESTION_CALENDARIO_FACTURACION_SQL.split())

    assert "ce.tipo_evento = 'F'" in sql
    assert "PARTITION BY COALESCE(ce.evento_padre_id, -ce.id), CAST(ce.fecha AS date)" in sql
    assert "ORDER BY ce.id" in sql
    assert "WHERE orden = 1 AND ISNULL(realizado, 0) = 0" in sql
    assert "LEFT JOIN Gestion.dbo.usuario u ON u.id = ce.usuario_operador_facturacion_id" in sql
