"""Conteo mensual de días de baja para el reporte de descuentos (paridad
discountedReport del legacy): recorre los días del mes; los descuentos solo
cuentan días hábiles (ni finde ni feriado) y computan 0.5 si la baja es de
medio día. Enfermedad y guardia cuentan días corridos (semántica de los
contadores por tipo del legacy — las guardias suelen caer en finde).
"""

from calendar import monthrange
from datetime import date, timedelta

from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia

_SABADO = 5


def _dias_del_mes(year: int, month: int) -> list[date]:
    primero = date(year, month, 1)
    total = monthrange(year, month)[1]
    return [primero + timedelta(days=i) for i in range(total)]


def _cobertura(ausencias: list[Ausencia], tipo: TipoAusencia, dia: date) -> Ausencia | None:
    for ausencia in ausencias:
        if ausencia.tipo is tipo and ausencia.cubre(dia):
            return ausencia
    return None


def dias_descontados_en_mes(
    ausencias: list[Ausencia], *, year: int, month: int, feriados: frozenset[date]
) -> float:
    total = 0.0
    for dia in _dias_del_mes(year, month):
        if dia.weekday() >= _SABADO or dia in feriados:
            continue
        match = _cobertura(ausencias, TipoAusencia.DESCUENTO_DIA, dia)
        if match is not None:
            total += 0.5 if match.half_day else 1.0
    return total


def dias_corridos_en_mes(
    ausencias: list[Ausencia], tipo: TipoAusencia, *, year: int, month: int
) -> int:
    return sum(
        1 for dia in _dias_del_mes(year, month) if _cobertura(ausencias, tipo, dia)
    )
