"""Tests de la ventana de escalado de alertas (horario laboral configurable)."""

from dataclasses import replace
from datetime import UTC, datetime

from src.modules.insumos.domain.services.alert_escalation import (
    escalation_cutoff,
    is_escalation_window,
)
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings

CON_HORARIO = InsumosSettings()  # 8 a 18, horario laboral activado


def _local(day: int, hour: int) -> datetime:
    """Junio de 2026: el 1 es lunes, el 6 sábado, el 7 domingo."""
    return datetime(2026, 6, day, hour, tzinfo=UTC)


def test_dentro_del_horario_laboral_se_escala() -> None:
    assert is_escalation_window(_local(3, 10), CON_HORARIO) is True


def test_de_noche_no_se_escala() -> None:
    """Escalar a las 3 AM solo produce un banner que nadie puede atender y que ya
    llega escalado a la mañana siguiente."""
    assert is_escalation_window(_local(3, 3), CON_HORARIO) is False
    assert is_escalation_window(_local(3, 18), CON_HORARIO) is False  # el fin es exclusivo


def test_el_fin_de_semana_no_se_escala() -> None:
    assert is_escalation_window(_local(6, 10), CON_HORARIO) is False
    assert is_escalation_window(_local(7, 10), CON_HORARIO) is False


def test_con_el_horario_laboral_desactivado_se_escala_siempre() -> None:
    sin_horario = replace(CON_HORARIO, alert_work_hours_enabled=False)

    assert is_escalation_window(_local(7, 3), sin_horario) is True


def test_la_ventana_sale_de_la_configuracion_no_esta_fija() -> None:
    nocturno = replace(CON_HORARIO, alert_work_hour_start=20, alert_work_hour_end=23)

    assert is_escalation_window(_local(3, 10), nocturno) is False
    assert is_escalation_window(_local(3, 21), nocturno) is True


def test_el_corte_se_mide_hacia_atras_desde_ahora() -> None:
    ahora = datetime(2026, 6, 3, 15, 0, tzinfo=UTC)

    cutoff = escalation_cutoff(ahora, replace(CON_HORARIO, alert_escalation_minutes=90))

    assert cutoff == datetime(2026, 6, 3, 13, 30, tzinfo=UTC)
