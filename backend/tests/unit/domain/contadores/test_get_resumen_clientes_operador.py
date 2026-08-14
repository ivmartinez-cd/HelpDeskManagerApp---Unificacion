"""Tests del resumen clientes+impresoras por operador (card de Inicio)."""

from datetime import date
from unittest.mock import AsyncMock

import pytest

from src.modules.contadores.application.use_cases.get_resumen_clientes_operador import (
    GetResumenClientesOperador,
    GetResumenClientesOperadorDependencies,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.domain.ports.parque_cliente_port import EmpresaSiges
from src.shared.domain.errors import ExternalServiceError

_HOY = date(2026, 8, 14)


def _event(event_id: str, cliente: str | None, operador_id: str | None) -> CalendarEvent:
    return CalendarEvent(
        id=event_id,
        title=f"[Facturación]: {cliente}",
        start="2026-08-10T00:00:00-03:00",
        cliente=cliente,
        operador_id=operador_id,
    )


def _calendar_mock(events: list[CalendarEvent]) -> AsyncMock:
    mock = AsyncMock()
    mock.list_events.return_value = events
    mock.list_operadores.return_value = [
        Operador(id="vipaez", nombre="Victor Paez", color="#888200"),
        Operador(id="mpollero", nombre="Marina Pollero", color="#123456"),
    ]
    return mock


def _alias_mock(alias: dict[str, list[int]] | None = None) -> AsyncMock:
    mock = AsyncMock()
    mock.list_all.return_value = alias or {}
    return mock


def _parque_mock(
    empresas: list[EmpresaSiges], impresoras: dict[int, int]
) -> AsyncMock:
    mock = AsyncMock()
    mock.list_empresas_activas.return_value = empresas
    mock.count_impresoras_by_empresa_ids.return_value = impresoras
    return mock


@pytest.mark.asyncio
async def test_agrupa_clientes_distintos_y_suma_impresoras() -> None:
    events = [
        _event("1", "ACME", "vipaez"),
        _event("2", "ACME", "vipaez"),  # repetido: cuenta una vez
        _event("3", "Globex", "vipaez"),
        _event("4", "ACME", "mpollero"),  # el mismo cliente puede estar en dos operadores
        _event("5", None, "vipaez"),  # sin cliente: se ignora
        _event("6", "Umbrella", None),  # sin operador: se ignora
    ]
    parque = _parque_mock(
        empresas=[
            EmpresaSiges(id=1, den_comercial="ACME"),
            EmpresaSiges(id=2, den_comercial="Globex"),
        ],
        impresoras={1: 10, 2: 3},
    )
    deps = GetResumenClientesOperadorDependencies(
        calendar=_calendar_mock(events), alias=_alias_mock(), parque=parque
    )

    resumen = await GetResumenClientesOperador(deps).execute(hoy=_HOY, dias_ventana=90)

    # cartera: ventana futura desde hoy, no el mes calendario
    assert resumen.desde == _HOY
    assert resumen.hasta == date(2026, 11, 12)
    assert resumen.total_clientes == 2  # ACME y Globex
    assert [f.operador_id for f in resumen.operadores] == ["vipaez", "mpollero"]
    vipaez, mpollero = resumen.operadores
    assert (vipaez.clientes, vipaez.impresoras, vipaez.sin_cruce) == (2, 13, [])
    assert (mpollero.clientes, mpollero.impresoras) == (1, 10)
    assert vipaez.operador_nombre == "Victor Paez"
    assert vipaez.operador_color == "#888200"
    assert resumen.total_impresoras == 23


@pytest.mark.asyncio
async def test_cliente_sin_cruce_se_informa_y_no_suma() -> None:
    events = [_event("1", "ACME", "vipaez"), _event("2", "Sin Cruce SRL", "vipaez")]
    parque = _parque_mock(
        empresas=[EmpresaSiges(id=1, den_comercial="ACME")], impresoras={1: 10}
    )
    deps = GetResumenClientesOperadorDependencies(
        calendar=_calendar_mock(events), alias=_alias_mock(), parque=parque
    )

    resumen = await GetResumenClientesOperador(deps).execute(hoy=_HOY, dias_ventana=90)

    fila = resumen.operadores[0]
    assert fila.clientes == 2
    assert fila.impresoras == 10
    assert fila.sin_cruce == ["Sin Cruce SRL"]


@pytest.mark.asyncio
async def test_alias_multiempresa_suma_todas_las_empresas() -> None:
    events = [_event("1", "Salta Refrescos", "vipaez")]
    parque = _parque_mock(empresas=[], impresoras={68: 59, 69: 48, 585: 42})
    deps = GetResumenClientesOperadorDependencies(
        calendar=_calendar_mock(events),
        alias=_alias_mock({"Salta Refrescos": [68, 69, 585]}),
        parque=parque,
    )

    resumen = await GetResumenClientesOperador(deps).execute(hoy=_HOY, dias_ventana=90)

    assert resumen.operadores[0].impresoras == 149
    assert resumen.operadores[0].sin_cruce == []


@pytest.mark.asyncio
async def test_operador_pool_excluido() -> None:
    events = [_event("1", "ACME", "contadores"), _event("2", "ACME", "vipaez")]
    parque = _parque_mock(
        empresas=[EmpresaSiges(id=1, den_comercial="ACME")], impresoras={1: 10}
    )
    deps = GetResumenClientesOperadorDependencies(
        calendar=_calendar_mock(events), alias=_alias_mock(), parque=parque
    )

    resumen = await GetResumenClientesOperador(deps).execute(
        hoy=_HOY, dias_ventana=90, exclude_operador_ids=frozenset({"contadores"})
    )

    assert [f.operador_id for f in resumen.operadores] == ["vipaez"]


@pytest.mark.asyncio
async def test_siges_caido_degrada_a_solo_clientes() -> None:
    events = [_event("1", "ACME", "vipaez")]
    parque = AsyncMock()
    parque.list_empresas_activas.side_effect = ExternalServiceError("MERCURIO caído")
    deps = GetResumenClientesOperadorDependencies(
        calendar=_calendar_mock(events), alias=_alias_mock(), parque=parque
    )

    resumen = await GetResumenClientesOperador(deps).execute(hoy=_HOY, dias_ventana=90)

    fila = resumen.operadores[0]
    assert (fila.clientes, fila.impresoras, fila.sin_cruce) == (1, None, [])
    assert resumen.total_impresoras is None


@pytest.mark.asyncio
async def test_sin_gateway_configurado_degrada_a_solo_clientes() -> None:
    events = [_event("1", "ACME", "vipaez")]
    deps = GetResumenClientesOperadorDependencies(
        calendar=_calendar_mock(events), alias=_alias_mock(), parque=None
    )

    resumen = await GetResumenClientesOperador(deps).execute(hoy=_HOY, dias_ventana=90)

    assert resumen.operadores[0].impresoras is None
    assert resumen.total_impresoras is None
