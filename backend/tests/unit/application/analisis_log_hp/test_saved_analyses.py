"""CRUD de análisis guardados con fan-out a telemetría, comparación contra log
nuevo, comparación entre snapshots y salud del equipo."""

import uuid
from datetime import timedelta

import pytest

from src.modules.analisis_log_hp.application.use_cases.saved_analyses import (
    CompareAnalysisWithLog,
    CompareSnapshots,
    CreateSavedAnalysis,
    DeleteSavedAnalysis,
    GetAnalysisHealth,
    GetSavedAnalysis,
    ListSavedAnalyses,
    UpdateSavedAnalysis,
    incident_to_summary,
)
from src.modules.analisis_log_hp.domain.entities.saved_analysis import TelemetryEvent
from src.modules.analisis_log_hp.domain.errors import SavedAnalysisNameInvalidError
from src.shared.domain.errors import NotFoundError
from tests.unit.application.analisis_log_hp.fakes import (
    NOW,
    FakeSavedAnalysisRepo,
    FakeTelemetryRepo,
    make_incident,
)


def test_incident_to_summary_usa_end_time_como_last_event_time() -> None:
    inc = make_incident("13.20", start=NOW - timedelta(hours=1), end=NOW, counter_range=(1, 9))
    d = incident_to_summary(inc)
    assert d["last_event_time"] == NOW.isoformat()
    assert d["counter_range"] == [1, 9]
    assert d["classification"] == "desc 13.20"


class TestCreateSavedAnalysis:
    async def test_guarda_resumenes_y_telemetria_con_serial_limpio(self) -> None:
        repo, tele = FakeSavedAnalysisRepo(), FakeTelemetryRepo()
        incidents = [make_incident("13.20", occurrences=2, counter_range=(10, 50))]

        saved = await CreateSavedAnalysis(repo, tele).execute(
            "mi análisis", "HP M404 (abc1)", incidents, "ERROR", ai_diagnosis="diag"
        )

        assert repo.rows[saved.id].incidents[0]["code"] == "13.20"
        assert saved.ai_diagnosis == "diag"
        assert len(tele.events) == 1
        ev = tele.events[0]
        assert (ev.device_serial, ev.saved_analysis_id) == ("ABC1", saved.id)
        assert (ev.counter, ev.occurrences, ev.event_time) == (50, 2, NOW)

    async def test_sin_equipo_no_escribe_telemetria(self) -> None:
        repo, tele = FakeSavedAnalysisRepo(), FakeTelemetryRepo()
        await CreateSavedAnalysis(repo, tele).execute("x", None, [make_incident()], "ERROR")
        assert tele.events == []

    async def test_nombre_solo_espacios_lanza_validacion(self) -> None:
        repo, tele = FakeSavedAnalysisRepo(), FakeTelemetryRepo()
        with pytest.raises(SavedAnalysisNameInvalidError):
            await CreateSavedAnalysis(repo, tele).execute("   ", None, [], "INFO")
        assert repo.rows == {}


class TestListGetUpdateDelete:
    async def test_list_delega_la_paginacion(self) -> None:
        repo = FakeSavedAnalysisRepo()
        repo.seed()
        repo.seed()
        items, total = await ListSavedAnalyses(repo).execute(1, 1)
        assert (total, len(items)) == (2, 1)

    async def test_get_devuelve_el_snapshot(self) -> None:
        repo = FakeSavedAnalysisRepo()
        snap = repo.seed()
        assert await GetSavedAnalysis(repo).execute(snap.id) == snap

    async def test_get_inexistente_lanza_not_found(self) -> None:
        with pytest.raises(NotFoundError):
            await GetSavedAnalysis(FakeSavedAnalysisRepo()).execute(uuid.uuid4())

    async def test_update_reemplaza_telemetria_del_analisis(self) -> None:
        repo = FakeSavedAnalysisRepo()
        snap = repo.seed()
        vieja = TelemetryEvent("SER1", snap.id, "OLD", None, "ERROR", 1, 1, NOW)
        ajena = TelemetryEvent("SER1", uuid.uuid4(), "OTRO", None, "ERROR", 1, 1, NOW)
        tele = FakeTelemetryRepo([vieja, ajena])

        nuevo = await UpdateSavedAnalysis(repo, tele).execute(
            snap.id, snap.name, "HP (SER1)", [make_incident("NEW")], "WARNING"
        )

        assert nuevo.global_severity == "WARNING"
        assert [e.code for e in tele.events] == ["OTRO", "NEW"]

    async def test_update_renombra_el_analisis(self) -> None:
        repo = FakeSavedAnalysisRepo()
        snap = repo.seed()

        nuevo = await UpdateSavedAnalysis(repo, FakeTelemetryRepo()).execute(
            snap.id, "  snap editado ", None, [], "INFO"
        )

        assert nuevo.name == "snap editado"
        assert repo.rows[snap.id].name == "snap editado"

    async def test_update_con_nombre_vacio_lanza_validacion_sin_tocar_nada(self) -> None:
        repo = FakeSavedAnalysisRepo()
        snap = repo.seed()
        tele = FakeTelemetryRepo([TelemetryEvent("S", snap.id, "OLD", None, "ERROR", 1, 1, NOW)])

        with pytest.raises(SavedAnalysisNameInvalidError):
            await UpdateSavedAnalysis(repo, tele).execute(snap.id, "", None, [], "INFO")

        assert repo.rows[snap.id].name == "snap"
        assert len(tele.events) == 1

    async def test_update_sin_equipo_solo_borra_telemetria(self) -> None:
        repo = FakeSavedAnalysisRepo()
        snap = repo.seed()
        tele = FakeTelemetryRepo([TelemetryEvent("S", snap.id, "OLD", None, "ERROR", 1, 1, NOW)])
        await UpdateSavedAnalysis(repo, tele).execute(
            snap.id, snap.name, None, [make_incident()], "ERROR"
        )
        assert tele.events == []

    async def test_update_inexistente_lanza_not_found(self) -> None:
        with pytest.raises(NotFoundError):
            await UpdateSavedAnalysis(FakeSavedAnalysisRepo(), FakeTelemetryRepo()).execute(
                uuid.uuid4(), "x", None, [], "INFO"
            )

    async def test_delete_borra_snapshot_y_telemetria(self) -> None:
        repo = FakeSavedAnalysisRepo()
        snap = repo.seed()
        tele = FakeTelemetryRepo([TelemetryEvent("S", snap.id, "A", None, "ERROR", 1, 1, NOW)])
        await DeleteSavedAnalysis(repo, tele).execute(snap.id)
        assert repo.rows == {}
        assert tele.events == []

    async def test_delete_inexistente_lanza_not_found(self) -> None:
        with pytest.raises(NotFoundError):
            await DeleteSavedAnalysis(FakeSavedAnalysisRepo(), FakeTelemetryRepo()).execute(
                uuid.uuid4()
            )


class TestCompareAnalysisWithLog:
    async def test_devuelve_diff_tendencia_y_dias_transcurridos(self) -> None:
        repo = FakeSavedAnalysisRepo()
        snap = repo.seed(
            incidents=[{"code": "A", "occurrences": 1, "severity": "ERROR"}],
            created_at=NOW - timedelta(days=400),
        )
        current = [make_incident("A", occurrences=5), make_incident("B")]

        result = await CompareAnalysisWithLog(repo).execute(snap.id, current, "ERROR", 6)

        assert result.diff["codigos_nuevos"] == ["B"]
        assert result.diff["tendencia"] == "empeoro"
        assert result.diff["diferencia_dias"] >= 400
        assert result.current_incidents[1]["code"] == "B"
        assert (result.current_global_severity, result.current_events_count) == ("ERROR", 6)

    async def test_snapshot_con_created_at_naive_no_rompe(self) -> None:
        repo = FakeSavedAnalysisRepo()
        snap = repo.seed(incidents=[], created_at=NOW.replace(tzinfo=None))
        result = await CompareAnalysisWithLog(repo).execute(snap.id, [], "INFO", 0)
        assert result.diff["tendencia"] == "estable"

    async def test_inexistente_lanza_not_found(self) -> None:
        with pytest.raises(NotFoundError):
            await CompareAnalysisWithLog(FakeSavedAnalysisRepo()).execute(
                uuid.uuid4(), [], "INFO", 0
            )


class TestCompareSnapshots:
    async def test_ordena_por_fecha_y_calcula_diff(self) -> None:
        repo = FakeSavedAnalysisRepo()
        nuevo = repo.seed(
            incidents=[{"code": "A", "occurrences": 4, "severity": "ERROR"}], created_at=NOW
        )
        viejo = repo.seed(
            incidents=[{"code": "A", "occurrences": 1, "severity": "ERROR"}],
            created_at=NOW - timedelta(days=3),
        )
        result = await CompareSnapshots(repo).execute(nuevo.id, viejo.id)
        assert (result["older"], result["newer"]) == (viejo, nuevo)
        assert result["diff"]["diferencia_dias"] == 3
        assert result["diff"]["tendencia"] == "empeoro"

    async def test_falta_uno_lanza_not_found(self) -> None:
        repo = FakeSavedAnalysisRepo()
        snap = repo.seed()
        with pytest.raises(NotFoundError):
            await CompareSnapshots(repo).execute(snap.id, uuid.uuid4())


class TestGetAnalysisHealth:
    async def test_evalua_salud_con_la_telemetria_del_serial(self) -> None:
        repo = FakeSavedAnalysisRepo()
        snap = repo.seed(equipment_identifier="HP (ser1)")
        eventos = [
            TelemetryEvent(
                "SER1", None, "13.20", None, "ERROR", 1, 1000 + i, NOW - timedelta(days=i)
            )
            for i in range(4)
        ]
        tele = FakeTelemetryRepo(eventos)
        result = await GetAnalysisHealth(repo, tele).execute(snap.id)
        assert result.health.status == "RED"
        assert result.events_count == 4

    async def test_sin_equipo_asociado_es_green(self) -> None:
        repo = FakeSavedAnalysisRepo()
        snap = repo.seed(equipment_identifier=None)
        result = await GetAnalysisHealth(repo, FakeTelemetryRepo()).execute(snap.id)
        assert (result.health.status, result.health.label) == ("GREEN", "Sin equipo asociado")

    async def test_identificador_solo_espacios_no_tiene_serial(self) -> None:
        repo = FakeSavedAnalysisRepo()
        snap = repo.seed(equipment_identifier="   ")
        result = await GetAnalysisHealth(repo, FakeTelemetryRepo()).execute(snap.id)
        assert (result.health.status, result.health.label) == ("GREEN", "Sin serial")

    async def test_inexistente_lanza_not_found(self) -> None:
        with pytest.raises(NotFoundError):
            await GetAnalysisHealth(FakeSavedAnalysisRepo(), FakeTelemetryRepo()).execute(
                uuid.uuid4()
            )
