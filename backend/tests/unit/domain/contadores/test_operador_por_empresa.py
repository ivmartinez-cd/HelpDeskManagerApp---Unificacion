from datetime import date, datetime

import pytest

from src.modules.contadores.application.use_cases.operador_por_empresa import (
    MapaOperadorPorEmpresa,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.domain.ports.parque_cliente_port import EmpresaSiges
from src.shared.domain.errors import ExternalServiceError

_HOY = date(2026, 8, 14)


def _event(id_: str, cliente: str, operador_id: str, start: str) -> CalendarEvent:
    return CalendarEvent(
        id=id_, title=cliente, start=start, operador_id=operador_id, cliente=cliente
    )


class _FakeCalendar:
    def __init__(self, events: list[CalendarEvent], operadores: list[Operador]) -> None:
        self._events = events
        self._operadores = operadores

    async def list_events(
        self, *, start_date: str, end_date: str, operador_id: str | None
    ) -> list[CalendarEvent]:
        return self._events

    async def list_operadores(self) -> list[Operador]:
        return self._operadores

    async def replace_events_in_range(self, **kwargs: object) -> None:
        raise NotImplementedError

    async def prune_operadores_not_in(self, operador_ids: list[str]) -> None:
        raise NotImplementedError

    async def replace_operadores(self, operadores: list[Operador]) -> None:
        raise NotImplementedError

    async def find_operador_by_nombre(self, nombre: str) -> Operador | None:
        raise NotImplementedError

    async def last_synced_at(self) -> datetime | None:
        raise NotImplementedError

    async def count_events(self) -> int:
        raise NotImplementedError


class _FakeAlias:
    def __init__(self, alias: dict[str, list[int]] | None = None) -> None:
        self._alias = alias or {}

    async def list_all(self) -> dict[str, list[int]]:
        return self._alias

    async def replace(self, cliente_gestion: str, siges_empresa_ids: list[int]) -> None:
        raise NotImplementedError


class _FakeParque:
    def __init__(self, empresas: list[EmpresaSiges], *, caido: bool = False) -> None:
        self._empresas = empresas
        self._caido = caido

    async def list_empresas_activas(self) -> list[EmpresaSiges]:
        if self._caido:
            raise ExternalServiceError("MERCURIO caído")
        return self._empresas

    async def count_impresoras_by_empresa_ids(self, empresa_ids: list[int]) -> dict[int, int]:
        raise NotImplementedError

    async def search_empresas_activas(self, texto: str) -> list[EmpresaSiges]:
        raise NotImplementedError


_OPERADORES = [
    Operador(id="vpaez", nombre="Victor Paez", color="#888200"),
    Operador(id="agomez", nombre="Ana Gomez", color="#112233"),
]

_EMPRESAS = [
    EmpresaSiges(id=10, den_comercial="Banco Bice"),
    EmpresaSiges(id=20, den_comercial="Adecoagro"),
]


@pytest.mark.asyncio
async def test_mapea_empresa_a_operador_via_nombre_normalizado() -> None:
    mapa = MapaOperadorPorEmpresa(
        _FakeCalendar([_event("1", "banco bice", "vpaez", "2026-08-20")], _OPERADORES),
        _FakeAlias(),
        _FakeParque(_EMPRESAS),
    )
    resultado = await mapa.build(hoy=_HOY)
    assert resultado[10].nombre == "Victor Paez"
    assert resultado[10].color == "#888200"
    assert 20 not in resultado


@pytest.mark.asyncio
async def test_evento_futuro_mas_proximo_gana_sobre_el_pasado() -> None:
    events = [
        _event("1", "Adecoagro", "agomez", "2026-08-13"),
        _event("2", "Adecoagro", "vpaez", "2026-08-20"),
        _event("3", "Adecoagro", "agomez", "2026-09-10"),
    ]
    mapa = MapaOperadorPorEmpresa(
        _FakeCalendar(events, _OPERADORES), _FakeAlias(), _FakeParque(_EMPRESAS)
    )
    resultado = await mapa.build(hoy=_HOY)
    assert resultado[20].nombre == "Victor Paez"


@pytest.mark.asyncio
async def test_alias_manual_gana_sobre_el_cruce_automatico() -> None:
    mapa = MapaOperadorPorEmpresa(
        _FakeCalendar([_event("1", "El Banco", "agomez", "2026-08-20")], _OPERADORES),
        _FakeAlias({"El Banco": [10]}),
        _FakeParque(_EMPRESAS),
    )
    resultado = await mapa.build(hoy=_HOY)
    assert resultado[10].nombre == "Ana Gomez"


@pytest.mark.asyncio
async def test_siges_caido_degrada_a_mapa_vacio() -> None:
    mapa = MapaOperadorPorEmpresa(
        _FakeCalendar([_event("1", "Banco Bice", "vpaez", "2026-08-20")], _OPERADORES),
        _FakeAlias(),
        _FakeParque(_EMPRESAS, caido=True),
    )
    assert await mapa.build(hoy=_HOY) == {}


@pytest.mark.asyncio
async def test_sin_eventos_no_consulta_siges() -> None:
    mapa = MapaOperadorPorEmpresa(
        _FakeCalendar([], _OPERADORES), _FakeAlias(), _FakeParque(_EMPRESAS, caido=True)
    )
    assert await mapa.build(hoy=_HOY) == {}
