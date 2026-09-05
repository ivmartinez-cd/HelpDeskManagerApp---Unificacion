"""Casos de borde de compare_service (diff, umbral +20 %, diff entre snapshots)
y de degradation_service (datetimes naive, ventana por páginas, estabilización
por páginas, mantenimiento sin fecha) no cubiertos por la caracterización base."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.modules.analisis_log_hp.domain.services.compare_service import (
    calculate_trend,
    compute_diff,
    diff_two_snapshots,
)
from src.modules.analisis_log_hp.domain.services.degradation_service import (
    evaluate_device_health,
)

_NOW = datetime(2026, 8, 16, 12, 0, tzinfo=UTC)


def _saved(code: str, occurrences: int, severity: str = "ERROR") -> dict[str, object]:
    return {"code": code, "occurrences": occurrences, "severity": severity}


@dataclass
class _Inc:
    code: str
    occurrences: int = 1
    severity: str = "ERROR"


class TestComputeDiff:
    def test_detecta_nuevos_desaparecidos_y_cambios(self) -> None:
        saved = [_saved("A", 1), _saved("B", 2)]
        current = {"A": _Inc("A", occurrences=3), "C": _Inc("C")}
        diff = compute_diff(saved, current)
        assert diff["codigos_nuevos"] == ["C"]
        assert diff["codigos_desaparecidos"] == ["B"]
        assert diff["cambios_ocurrencias"] == [
            {"code": "A", "saved_occurrences": 1, "current_occurrences": 3, "delta": 2}
        ]

    def test_acepta_enteros_como_ocurrencias_actuales(self) -> None:
        diff = compute_diff([_saved("A", 1)], {"A": 4})
        assert diff["cambios_ocurrencias"][0]["delta"] == 3

    def test_ocurrencias_guardadas_nulas_cuentan_como_cero(self) -> None:
        diff = compute_diff([{"code": "A", "occurrences": None}], {"A": _Inc("A", 2)})
        assert diff["cambios_ocurrencias"][0]["saved_occurrences"] == 0


class TestCalculateTrendUmbrales:
    def test_total_de_errores_sube_20_por_ciento_empeora(self) -> None:
        saved = [_saved("A", 5), _saved("B", 5)]
        current = {"A": _Inc("A", 6), "B": _Inc("B", 6)}
        diff = compute_diff(saved, current)
        assert calculate_trend(saved, current, diff) == "empeoro"

    def test_sube_menos_de_20_por_ciento_es_estable(self) -> None:
        saved = [_saved("A", 10)]
        current = {"A": _Inc("A", 11)}
        diff = compute_diff(saved, current)
        assert calculate_trend(saved, current, diff) == "estable"

    def test_warning_nuevo_no_empeora(self) -> None:
        saved = [_saved("A", 1)]
        current = {"A": _Inc("A"), "W": _Inc("W", severity="WARNING")}
        diff = compute_diff(saved, current)
        assert calculate_trend(saved, current, diff) == "estable"

    def test_severidad_actual_como_string_se_acepta(self) -> None:
        saved = [_saved("A", 1)]
        current = {"A": "ERROR", "B": "ERROR"}
        diff = compute_diff(saved, current)
        assert calculate_trend(saved, current, diff) == "empeoro"

    def test_error_desaparecido_pero_con_error_nuevo_no_mejora(self) -> None:
        saved = [_saved("A", 3)]
        current = {"B": _Inc("B", 1)}
        diff = compute_diff(saved, current)
        assert calculate_trend(saved, current, diff) == "empeoro"


class TestDiffTwoSnapshots:
    def test_diff_completo_con_tendencia_y_dias(self) -> None:
        older = [_saved("A", 1), _saved("B", 2)]
        newer = [_saved("A", 5), _saved("C", 1)]
        diff = diff_two_snapshots(older, newer, diferencia_dias=7)
        assert diff["codigos_nuevos"] == ["C"]
        assert diff["codigos_desaparecidos"] == ["B"]
        assert diff["cambios_ocurrencias"][0]["delta"] == 4
        assert diff["diferencia_dias"] == 7
        assert diff["tendencia"] == "empeoro"

    def test_snapshots_iguales_son_estables(self) -> None:
        inc = [_saved("A", 2)]
        assert diff_two_snapshots(inc, list(inc), 0)["tendencia"] == "estable"

    def test_error_que_desaparece_mejora(self) -> None:
        older = [_saved("A", 3), _saved("B", 1)]
        newer = [_saved("B", 1)]
        assert diff_two_snapshots(older, newer, 1)["tendencia"] == "mejoro"


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
    changed_at: datetime | None = None


class TestEvaluateDeviceHealthBordes:
    def test_datetimes_naive_se_tratan_como_utc(self) -> None:
        naive_now = datetime(2026, 8, 16, 12, 0)
        ev = _Ev("41.03", event_time=datetime(2026, 8, 15, 12, 0))
        salud = evaluate_device_health([ev], now=naive_now)
        assert salud.status == "YELLOW"

    def test_mantenimiento_sin_fecha_no_dispara_post_reparacion(self) -> None:
        ev = _Ev("41.03", event_time=_NOW - timedelta(days=1))
        salud = evaluate_device_health([ev], [_Maint(changed_at=None)], now=_NOW)
        assert salud.triggered_rule != "post_repair"

    def test_error_anterior_al_mantenimiento_no_es_post_reparacion(self) -> None:
        maint = _Maint(changed_at=_NOW - timedelta(days=1))
        ev = _Ev("41.03", event_time=_NOW - timedelta(days=2))
        salud = evaluate_device_health([ev], [maint], now=_NOW)
        assert salud.triggered_rule != "post_repair"

    def test_recurrencia_por_ventana_de_paginas_aunque_sean_viejos(self) -> None:
        viejos = [
            _Ev("13.20", event_time=_NOW - timedelta(days=60 + i), counter=9000 + i)
            for i in range(4)
        ]
        reciente = _Ev("INFO", severity="INFO", counter=10_000, event_time=_NOW)
        salud = evaluate_device_health([*viejos, reciente], now=_NOW)
        assert salud.triggered_rule == "recurrence"
        assert "13.20" in salud.reason

    def test_recurrencia_suma_ocurrencias_del_evento(self) -> None:
        ev = _Ev("13.20", occurrences=4, event_time=_NOW - timedelta(days=1))
        salud = evaluate_device_health([ev], now=_NOW)
        assert salud.status == "RED"
        assert "4 veces" in salud.reason

    def test_contador_cero_no_cuenta_para_ventana_de_paginas(self) -> None:
        viejos = [
            _Ev("13.20", event_time=_NOW - timedelta(days=60 + i), counter=0) for i in range(4)
        ]
        reciente = _Ev("INFO", severity="INFO", counter=10_000, event_time=_NOW)
        salud = evaluate_device_health([*viejos, reciente], now=_NOW)
        assert salud.triggered_rule == "stable"

    def test_estabilizacion_por_paginas_aunque_sea_reciente(self) -> None:
        crit = _Ev("13.20", event_time=_NOW - timedelta(days=1), counter=1000)
        reciente = _Ev("INFO", severity="INFO", counter=20_000, event_time=_NOW)
        salud = evaluate_device_health([crit, reciente], now=_NOW)
        assert salud.status == "GREEN"
        assert "páginas" in salud.reason

    def test_dedup_conserva_el_evento_con_mas_ocurrencias(self) -> None:
        t = _NOW - timedelta(days=1)
        dup = [_Ev("13.20", event_time=t, occurrences=1), _Ev("13.20", event_time=t, occurrences=5)]
        salud = evaluate_device_health(dup, now=_NOW)
        assert "5 veces" in salud.reason

    def test_severidad_critical_cuenta_como_critica(self) -> None:
        ev = _Ev("13.20", severity="critical", event_time=_NOW - timedelta(days=1))
        assert evaluate_device_health([ev], now=_NOW).status == "YELLOW"

    def test_expone_los_contadores_que_uso_la_regla(self) -> None:
        # Caso QA 2026-09-05: 2 ERROR viejos → GREEN por R3; la UI necesita ver
        # los días/páginas que justificaron el veredicto.
        viejos = [
            _Ev("13.20", occurrences=2, counter=1000, event_time=_NOW - timedelta(days=33)),
            _Ev("49.4C", counter=1000, event_time=_NOW - timedelta(days=40)),
        ]
        salud = evaluate_device_health(viejos, now=_NOW)
        assert salud.triggered_rule == "stable"
        assert (salud.critical_events_count, salud.critical_occurrences) == (2, 3)
        assert (salud.days_since_last_critical, salud.pages_since_last_critical) == (33, 0)

    def test_sin_criticos_los_contadores_quedan_en_cero(self) -> None:
        salud = evaluate_device_health([_Ev("INFO", severity="INFO")], now=_NOW)
        assert (salud.critical_events_count, salud.critical_occurrences) == (0, 0)
        assert salud.days_since_last_critical is None
        assert salud.pages_since_last_critical is None
