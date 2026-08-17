"""Caracterización de los servicios de dominio puros de analisis-log-hp:
salud del equipo (reglas R1/R2/R3), agrupado de incidentes y tendencia."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.modules.analisis_log_hp.domain.entities.log_event import EnrichedEvent
from src.modules.analisis_log_hp.domain.services.analysis_service import analyze_events
from src.modules.analisis_log_hp.domain.services.compare_service import (
    calculate_trend,
    compute_diff,
)
from src.modules.analisis_log_hp.domain.services.degradation_service import (
    evaluate_device_health,
)

_NOW = datetime(2026, 8, 16, 12, 0, tzinfo=UTC)


@dataclass
class _Ev:
    code: str
    severity: str = "ERROR"
    occurrences: int = 1
    counter: int = 1000
    event_time: datetime = _NOW


@dataclass
class _Maint:
    code: str = "MANT"
    severity: str = "INFO"
    occurrences: int = 1
    counter: int = 0
    event_time: datetime = _NOW
    changed_at: datetime = _NOW


class TestEvaluateDeviceHealth:
    def test_sin_eventos_es_green(self) -> None:
        salud = evaluate_device_health([], now=_NOW)
        assert salud.status == "GREEN"
        assert salud.triggered_rule is None

    def test_error_post_reparacion_es_red(self) -> None:
        maint = _Maint(changed_at=_NOW - timedelta(days=2))
        error = _Ev("13.20.01", event_time=_NOW - timedelta(days=1))
        salud = evaluate_device_health([error], [maint], now=_NOW)
        assert salud.status == "RED"
        assert salud.triggered_rule == "post_repair"

    def test_recurrencia_supera_umbral_es_red(self) -> None:
        eventos = [
            _Ev("41.03", event_time=_NOW - timedelta(days=i), counter=5000 + i)
            for i in range(4)
        ]
        salud = evaluate_device_health(eventos, now=_NOW)
        assert salud.status == "RED"
        assert salud.triggered_rule == "recurrence"

    def test_critico_viejo_estabilizado_es_green(self) -> None:
        viejo = _Ev("41.03", event_time=_NOW - timedelta(days=30), counter=1000)
        reciente_info = _Ev(
            "INFO1", severity="INFO", event_time=_NOW, counter=20_000
        )
        salud = evaluate_device_health([viejo, reciente_info], now=_NOW)
        assert salud.status == "GREEN"
        assert salud.triggered_rule == "stable"

    def test_critico_reciente_sin_umbral_es_yellow(self) -> None:
        reciente = _Ev("41.03", event_time=_NOW - timedelta(days=1), counter=1000)
        salud = evaluate_device_health([reciente], now=_NOW)
        assert salud.status == "YELLOW"

    def test_dedup_por_code_y_hora_no_cuenta_doble(self) -> None:
        misma_hora = _NOW - timedelta(days=1)
        duplicados = [
            _Ev("41.03", event_time=misma_hora, occurrences=1, counter=1000)
            for _ in range(5)
        ]
        salud = evaluate_device_health(duplicados, now=_NOW)
        assert salud.triggered_rule != "recurrence"


def _evento(
    code: str,
    tipo: str = "ERROR",
    ts: datetime = _NOW,
    counter: int = 100,
    descripcion: str | None = None,
    solucion_url: str | None = None,
) -> EnrichedEvent:
    return EnrichedEvent(
        type=tipo,
        code=code,
        timestamp=ts,
        counter=counter,
        firmware=None,
        help_reference=None,
        code_description=descripcion,
        code_solution_url=solucion_url,
        code_solution_content="contenido" if solucion_url else None,
    )


class TestAnalyzeEvents:
    def test_sin_eventos(self) -> None:
        resultado = analyze_events([])
        assert resultado.incidents == ()
        assert resultado.global_severity == "INFO"

    def test_un_incidente_por_codigo_con_severidad_maxima(self) -> None:
        eventos = [
            _evento("13.20", tipo="WARNING", ts=_NOW - timedelta(hours=2), counter=90),
            _evento("13.20", tipo="ERROR", ts=_NOW, counter=110),
            _evento("INFO9", tipo="INFO"),
        ]
        resultado = analyze_events(eventos)
        assert len(resultado.incidents) == 2
        inc = next(i for i in resultado.incidents if i.code == "13.20")
        assert inc.severity == "ERROR"
        assert inc.occurrences == 2
        assert inc.counter_range == (90, 110)
        assert resultado.global_severity == "ERROR"

    def test_clasificacion_y_solucion_del_primer_evento_con_dato(self) -> None:
        eventos = [
            _evento("13.20", ts=_NOW - timedelta(hours=1)),
            _evento("13.20", descripcion="  Atasco de papel  ", solucion_url=" http://sds/x "),
        ]
        inc = analyze_events(eventos).incidents[0]
        assert inc.classification == "Atasco de papel"
        assert inc.sds_link == "http://sds/x"
        assert inc.sds_solution_content == "contenido"

    def test_tipo_desconocido_cae_a_info(self) -> None:
        resultado = analyze_events([_evento("X1", tipo="RARO")])
        assert resultado.global_severity == "INFO"
        assert resultado.incidents[0].severity == "INFO"


def _saved(code: str, occurrences: int, severity: str = "ERROR") -> dict[str, object]:
    return {"code": code, "occurrences": occurrences, "severity": severity}


class TestCalculateTrend:
    def test_error_nuevo_empeora(self) -> None:
        saved = [_saved("A", 1)]
        current = {"A": _Ev("A", occurrences=1), "B": _Ev("B", occurrences=1)}
        diff = compute_diff(saved, current)
        assert calculate_trend(saved, current, diff) == "empeoro"

    def test_delta_tres_o_mas_empeora(self) -> None:
        saved = [_saved("A", 1)]
        current = {"A": _Ev("A", occurrences=4)}
        diff = compute_diff(saved, current)
        assert calculate_trend(saved, current, diff) == "empeoro"

    def test_de_cero_errores_a_alguno_empeora(self) -> None:
        saved = [_saved("W", 5, severity="WARNING")]
        current = {"W": _Ev("W", severity="WARNING", occurrences=5), "E": _Ev("E")}
        diff = compute_diff(saved, current)
        assert calculate_trend(saved, current, diff) == "empeoro"

    def test_error_desaparecido_y_total_abajo_mejora(self) -> None:
        saved = [_saved("A", 3), _saved("B", 2)]
        current = {"B": _Ev("B", occurrences=2)}
        diff = compute_diff(saved, current)
        assert calculate_trend(saved, current, diff) == "mejoro"

    def test_sin_cambios_es_estable(self) -> None:
        saved = [_saved("A", 2)]
        current = {"A": _Ev("A", occurrences=2)}
        diff = compute_diff(saved, current)
        assert calculate_trend(saved, current, diff) == "estable"
