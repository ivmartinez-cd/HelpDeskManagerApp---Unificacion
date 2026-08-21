from datetime import UTC, date, datetime

import pytest

from src.modules.contadores.application.use_cases.filtrar_pendientes_periodo_por_operador import (
    FiltrarPendientesPeriodoPorOperador,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.clientes_pendientes_periodo import (
    ClientesPendientesPeriodo,
)
from src.modules.contadores.domain.entities.operador import Operador

_HOY = date(2026, 8, 21)
_CONSULTADO_EN = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)


class _FakeRepository:
    def __init__(
        self, operadores: dict[str, Operador], eventos_por_operador: dict[str, list[str]]
    ) -> None:
        self._operadores = operadores
        self._eventos_por_operador = eventos_por_operador

    async def find_operador_by_nombre(self, nombre: str) -> Operador | None:
        return self._operadores.get(nombre)

    async def list_events(
        self, *, start_date: str, end_date: str, operador_id: str | None
    ) -> list[CalendarEvent]:
        clientes = self._eventos_por_operador.get(operador_id or "", [])
        return [
            CalendarEvent(id=f"e{i}", title="X", start="2026-08-21T00:00:00-03:00", cliente=c)
            for i, c in enumerate(clientes)
        ]


def _resultado(*grupos: str) -> ClientesPendientesPeriodo:
    return ClientesPendientesPeriodo(periodo="2026-07", grupos=grupos, consultado_en=_CONSULTADO_EN)


@pytest.mark.asyncio
async def test_superadmin_ve_todos_los_grupos() -> None:
    repo = _FakeRepository({}, {})
    resultado = _resultado("Le Pain Quotidien", "Vitalcan SA")
    filtrado = await FiltrarPendientesPeriodoPorOperador(repo).execute(
        resultado, is_superadmin=True, full_name="Cualquiera", hoy=_HOY, dias_ventana=90
    )
    assert filtrado.grupos == resultado.grupos


@pytest.mark.asyncio
async def test_operador_regular_solo_ve_los_grupos_de_su_cartera() -> None:
    operador = Operador(id="op1", nombre="Juan Perez")
    repo = _FakeRepository(
        {"Juan Perez": operador}, {"op1": ["Vitalcan SA"]}
    )
    resultado = _resultado("Le Pain Quotidien", "Vitalcan SA")
    filtrado = await FiltrarPendientesPeriodoPorOperador(repo).execute(
        resultado, is_superadmin=False, full_name="Juan Perez", hoy=_HOY, dias_ventana=90
    )
    assert filtrado.grupos == ("Vitalcan SA",)
    assert filtrado.periodo == resultado.periodo


@pytest.mark.asyncio
async def test_sin_operador_propio_no_muestra_nada() -> None:
    repo = _FakeRepository({}, {})
    resultado = _resultado("Le Pain Quotidien")
    filtrado = await FiltrarPendientesPeriodoPorOperador(repo).execute(
        resultado, is_superadmin=False, full_name="Sin Mapear", hoy=_HOY, dias_ventana=90
    )
    assert filtrado.grupos == ()


@pytest.mark.asyncio
async def test_lista_vacia_no_consulta_el_operador() -> None:
    repo = _FakeRepository({}, {})
    resultado = _resultado()
    filtrado = await FiltrarPendientesPeriodoPorOperador(repo).execute(
        resultado, is_superadmin=False, full_name="Juan Perez", hoy=_HOY, dias_ventana=90
    )
    assert filtrado.grupos == ()


@pytest.mark.asyncio
async def test_cruza_por_alias_manual() -> None:
    operador = Operador(id="op1", nombre="Juan Perez")
    repo = _FakeRepository({"Juan Perez": operador}, {"op1": ["JBS"]})
    resultado = _resultado("JBS Leather Argentina S.A.")
    filtrado = await FiltrarPendientesPeriodoPorOperador(repo).execute(
        resultado, is_superadmin=False, full_name="Juan Perez", hoy=_HOY, dias_ventana=90
    )
    assert filtrado.grupos == ("JBS Leather Argentina S.A.",)
