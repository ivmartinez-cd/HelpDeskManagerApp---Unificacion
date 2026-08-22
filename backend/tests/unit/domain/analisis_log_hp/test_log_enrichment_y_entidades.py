"""Enriquecimiento con el catálogo, extracción de serial, errores de dominio,
permisos bien conocidos y serialización de IncidentSummary."""

from datetime import UTC, datetime

import pytest

from src.modules.analisis_log_hp.domain import well_known_permissions as perms
from src.modules.analisis_log_hp.domain.entities.error_code import ErrorCode
from src.modules.analisis_log_hp.domain.entities.log_event import LogEvent
from src.modules.analisis_log_hp.domain.entities.saved_analysis import IncidentSummary
from src.modules.analisis_log_hp.domain.errors import (
    ErrorCodeNotFoundError,
    LogParseError,
    SavedAnalysisNotFoundError,
)
from src.modules.analisis_log_hp.domain.services.log_enrichment import (
    enrich_events,
    extract_serial_number,
)

_NOW = datetime(2026, 8, 16, 12, 0, tzinfo=UTC)


def _error_code(code: str = "13.20") -> ErrorCode:
    return ErrorCode(
        code=code,
        severity="ERROR",
        description="Atasco",
        solution_url="http://sds/13.20",
        solution_content="<p>contenido</p>",
        created_at=_NOW,
        updated_at=_NOW,
    )


def _event(code: str) -> LogEvent:
    return LogEvent(
        type="ERROR", code=code, timestamp=_NOW, counter=10, firmware="FW", help_reference=None
    )


class TestEnrichEvents:
    def test_evento_catalogado_copia_datos_del_catalogo(self) -> None:
        enriched = enrich_events([_event("13.20")], {"13.20": _error_code()})
        evt = enriched[0]
        assert (evt.code_severity, evt.code_description) == ("ERROR", "Atasco")
        assert evt.code_solution_url == "http://sds/13.20"
        assert evt.code_solution_content == "<p>contenido</p>"

    def test_evento_sin_catalogo_deja_campos_none_y_conserva_el_resto(self) -> None:
        evt = enrich_events([_event("99.99")], {})[0]
        assert evt.code_severity is None
        assert evt.code_solution_url is None
        assert (evt.type, evt.code, evt.counter, evt.firmware) == ("ERROR", "99.99", 10, "FW")

    def test_conserva_el_orden_de_los_eventos(self) -> None:
        enriched = enrich_events([_event("B"), _event("A")], {})
        assert [e.code for e in enriched] == ["B", "A"]


class TestExtractSerialNumber:
    @pytest.mark.parametrize(
        ("valor", "esperado"),
        [
            ("HP LaserJet M404 (abc123)", "ABC123"),
            ("  serie-1  ", "SERIE-1"),
            ("Modelo ( xyz )", "XYZ"),
            ("", None),
            (None, None),
        ],
    )
    def test_extrae_serial_entre_parentesis_o_usa_el_valor(
        self, valor: str | None, esperado: str | None
    ) -> None:
        assert extract_serial_number(valor) == esperado


class TestErroresDeDominio:
    def test_error_code_not_found_incluye_el_codigo(self) -> None:
        err = ErrorCodeNotFoundError("13.20")
        assert "13.20" in str(err)
        assert err.default_code == "ERROR_CODE_NOT_FOUND"

    def test_saved_analysis_not_found_tiene_mensaje_fijo(self) -> None:
        err = SavedAnalysisNotFoundError()
        assert "no encontrado" in str(err)
        assert err.default_code == "SAVED_ANALYSIS_NOT_FOUND"

    def test_log_parse_error_es_error_de_dominio(self) -> None:
        assert LogParseError.default_code == "LOG_PARSE_ERROR"


class TestIncidentSummary:
    def test_to_dict_expone_todos_los_campos(self) -> None:
        summary = IncidentSummary(
            code="13.20",
            classification="Atasco",
            severity="ERROR",
            occurrences=2,
            start_time="2026-08-01T00:00:00",
            end_time="2026-08-02T00:00:00",
            counter_range=[1, 2],
            sds_link=None,
            last_event_time="2026-08-02T00:00:00",
        )
        d = summary.to_dict()
        assert d["code"] == "13.20"
        assert d["counter_range"] == [1, 2]
        assert d["last_event_time"] == "2026-08-02T00:00:00"
        assert set(d) == {
            "code", "classification", "severity", "occurrences", "start_time",
            "end_time", "counter_range", "sds_link", "last_event_time",
        }


def test_permisos_del_modulo_usan_la_clave_analisis_log_hp() -> None:
    assert perms.VIEW.module.value == "analisis-log-hp"
    assert perms.MANAGE.action.value == "manage"
