"""Análisis guardados (JSONB de incidentes) y telemetría por serial contra
Postgres de test: round-trips, paginación por fecha, update parcial y deletes."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analisis_log_hp.domain.entities.saved_analysis import TelemetryEvent
from src.modules.analisis_log_hp.infrastructure.repositories.sqlalchemy_saved_analysis_repository import (  # noqa: E501
    SqlAlchemySavedAnalysisRepository,
)
from src.modules.analisis_log_hp.infrastructure.repositories.sqlalchemy_telemetry_repository import (  # noqa: E501
    SqlAlchemyTelemetryRepository,
)

_INC = [{"code": "13.20", "occurrences": 2, "severity": "ERROR", "counter_range": [1, 9]}]
_T0 = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)


async def test_create_y_get_by_id_round_trip(db_session: AsyncSession) -> None:
    repo = SqlAlchemySavedAnalysisRepository(db_session)

    creado = await repo.create("snap", "HP (SER1)", _INC, "ERROR", ai_diagnosis="diag")
    leido = await repo.get_by_id(creado.id)

    assert leido is not None
    assert (leido.name, leido.equipment_identifier, leido.global_severity) == (
        "snap", "HP (SER1)", "ERROR"
    )
    assert leido.incidents == _INC
    assert leido.ai_diagnosis == "diag"
    assert leido.created_at.tzinfo is not None


async def test_get_by_id_inexistente_devuelve_none(db_session: AsyncSession) -> None:
    repo = SqlAlchemySavedAnalysisRepository(db_session)
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_list_page_ordena_del_mas_nuevo_al_mas_viejo(db_session: AsyncSession) -> None:
    repo = SqlAlchemySavedAnalysisRepository(db_session)
    primero = await repo.create("primero", None, [], "INFO")
    segundo = await repo.create("segundo", None, [], "INFO")

    items, total = await repo.list_page(page=1, size=1)

    assert total == 2
    assert [s.id for s in items] == [segundo.id]
    otros_items, _ = await repo.list_page(page=2, size=1)
    assert [s.id for s in otros_items] == [primero.id]


async def test_update_reemplaza_incidentes_y_conserva_diagnostico_si_no_viene(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemySavedAnalysisRepository(db_session)
    creado = await repo.create("snap", None, _INC, "ERROR", ai_diagnosis="diag")

    sin_diag = await repo.update(creado.id, [], "INFO")
    con_diag = await repo.update(creado.id, [], "INFO", ai_diagnosis="nuevo")

    assert sin_diag is not None and (sin_diag.incidents, sin_diag.ai_diagnosis) == ([], "diag")
    assert con_diag is not None and con_diag.ai_diagnosis == "nuevo"
    assert await repo.update(uuid.uuid4(), [], "INFO") is None


async def test_delete_devuelve_true_solo_si_existia(db_session: AsyncSession) -> None:
    repo = SqlAlchemySavedAnalysisRepository(db_session)
    creado = await repo.create("snap", None, [], "INFO")

    assert await repo.delete(creado.id) is True
    assert await repo.get_by_id(creado.id) is None
    assert await repo.delete(creado.id) is False


def _evento(serial: str, analysis_id: uuid.UUID | None, code: str, t: datetime) -> TelemetryEvent:
    return TelemetryEvent(
        device_serial=serial, saved_analysis_id=analysis_id, code=code,
        classification="desc", severity="ERROR", occurrences=2, counter=500, event_time=t,
    )


async def test_telemetria_add_y_get_por_serial_ordenada_por_fecha(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyTelemetryRepository(db_session)
    aid = uuid.uuid4()
    await repo.add_events([
        _evento("SER1", aid, "B", datetime(2026, 8, 2, tzinfo=UTC)),
        _evento("SER1", None, "A", _T0),
        _evento("OTRO", aid, "C", _T0),
    ])

    eventos = await repo.get_events_by_serial("SER1")

    assert [e.code for e in eventos] == ["A", "B"]
    ev = eventos[1]
    assert (ev.saved_analysis_id, ev.classification, ev.occurrences, ev.counter) == (
        aid, "desc", 2, 500
    )
    assert ev.event_time == datetime(2026, 8, 2, tzinfo=UTC)


async def test_telemetria_add_vacio_no_falla(db_session: AsyncSession) -> None:
    repo = SqlAlchemyTelemetryRepository(db_session)
    await repo.add_events([])
    assert await repo.get_events_by_serial("NADIE") == []


async def test_telemetria_delete_by_analysis_id_borra_solo_ese_analisis(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyTelemetryRepository(db_session)
    aid, otro = uuid.uuid4(), uuid.uuid4()
    await repo.add_events([
        _evento("SER1", aid, "A", _T0),
        _evento("SER1", aid, "B", _T0),
        _evento("SER1", otro, "C", _T0),
    ])

    borrados = await repo.delete_by_analysis_id(aid)

    assert borrados == 2
    assert [e.code for e in await repo.get_events_by_serial("SER1")] == ["C"]
    assert await repo.delete_by_analysis_id(aid) == 0
