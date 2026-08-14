"""Round-trip del repo de calendario (eventos + operadores) contra Postgres."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.infrastructure.repositories.sqlalchemy_calendario_repository import (
    SqlAlchemyCalendarEventRepository,
)


def _event(
    gestion_id: str, *, start: str = "2026-08-14", operador: str = "vipaez"
) -> CalendarEvent:
    return CalendarEvent(
        id=gestion_id,
        title=f"Evento {gestion_id}",
        start=start,
        operador_id=operador,
        cliente="YAGUAR",
        content_tooltip="Faltantes a <mail@cliente.com>",
    )


async def test_replace_y_list_events_filtra_por_rango_y_operador(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyCalendarEventRepository(db_session)
    await repo.replace_events_in_range(
        start_date="2026-08-01",
        end_date="2026-08-31",
        events=[
            _event("1", start="2026-08-10"),
            _event("2", start="2026-08-20", operador="otro"),
        ],
    )

    todos = await repo.list_events(start_date="2026-08-01", end_date="2026-08-31", operador_id=None)
    assert [e.id for e in todos] == ["1", "2"]
    assert todos[0].content_tooltip == "Faltantes a <mail@cliente.com>"

    solo_vipaez = await repo.list_events(
        start_date="2026-08-01", end_date="2026-08-31", operador_id="vipaez"
    )
    assert [e.id for e in solo_vipaez] == ["1"]

    primera_quincena = await repo.list_events(
        start_date="2026-08-01", end_date="2026-08-15", operador_id=None
    )
    assert [e.id for e in primera_quincena] == ["1"]
    assert await repo.count_events() == 2
    assert await repo.last_synced_at() is not None


async def test_replace_events_es_full_replace_del_rango(db_session: AsyncSession) -> None:
    repo = SqlAlchemyCalendarEventRepository(db_session)
    await repo.replace_events_in_range(
        start_date="2026-08-01", end_date="2026-08-31", events=[_event("viejo")]
    )

    await repo.replace_events_in_range(
        start_date="2026-08-01", end_date="2026-08-31", events=[_event("nuevo")]
    )

    eventos = await repo.list_events(
        start_date="2026-08-01", end_date="2026-08-31", operador_id=None
    )
    assert [e.id for e in eventos] == ["nuevo"]


async def test_list_events_dedupea_por_gestion_id(db_session: AsyncSession) -> None:
    repo = SqlAlchemyCalendarEventRepository(db_session)
    # Mismo gestion_event_id bajo dos operadores (copia vieja de un cambio de
    # operador en Gestión): en lectura queda una sola.
    await repo.replace_events_in_range(
        start_date="2026-08-01",
        end_date="2026-08-31",
        events=[_event("dup", operador="vipaez"), _event("dup", operador="otro")],
    )

    eventos = await repo.list_events(
        start_date="2026-08-01", end_date="2026-08-31", operador_id=None
    )
    assert [e.id for e in eventos] == ["dup"]


async def test_operadores_upsert_busqueda_normalizada_y_prune(db_session: AsyncSession) -> None:
    repo = SqlAlchemyCalendarEventRepository(db_session)
    await repo.replace_operadores(
        [
            Operador(id="vipaez", nombre="Victor Páez", color="#888200"),
            Operador(id="otro", nombre="Otro Op", color=None),
        ]
    )
    # Upsert: re-insertar el mismo id actualiza nombre/color en vez de duplicar.
    await repo.replace_operadores([Operador(id="vipaez", nombre="Victor Paez", color="#111111")])

    operadores = {o.id: o for o in await repo.list_operadores()}
    assert set(operadores) == {"vipaez", "otro"}
    assert operadores["vipaez"].color == "#111111"

    # La búsqueda por nombre ignora acentos/mayúsculas/espacios repetidos.
    encontrado = await repo.find_operador_by_nombre("  víctor   PAEZ ")
    assert encontrado is not None and encontrado.id == "vipaez"
    assert await repo.find_operador_by_nombre("Nadie Conocido") is None

    await repo.replace_events_in_range(
        start_date="2026-08-01", end_date="2026-08-31", events=[_event("1", operador="otro")]
    )
    await repo.prune_operadores_not_in(["vipaez"])
    assert [o.id for o in await repo.list_operadores()] == ["vipaez"]
    assert await repo.count_events() == 0  # los eventos del operador podado se van con él
