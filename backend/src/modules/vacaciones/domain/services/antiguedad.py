"""Días anuales de vacaciones según antigüedad (cycle.service.ts legacy).

La antigüedad se proyecta a una fecha de referencia (el 1/1 del año del ciclo)
con el divisor 365.25 del legacy; los tiers son `min` inclusive / `max`
exclusivo y si la antigüedad supera el último tier se devuelve el último.
"""

from collections.abc import Sequence
from datetime import date

from src.modules.vacaciones.domain.value_objects.seniority_tier import (
    DEFAULT_TIERS,
    SeniorityTier,
)

_DIAS_POR_ANIO = 365.25


def dias_por_antiguedad(
    hire_date: date, referencia: date, tiers: Sequence[SeniorityTier]
) -> int:
    anios = (referencia - hire_date).days / _DIAS_POR_ANIO
    lista = tiers if tiers else DEFAULT_TIERS
    ordenados = sorted(lista, key=lambda t: t.min_years)
    for tier in ordenados:
        if tier.min_years <= anios < tier.max_years:
            return tier.days
    return ordenados[-1].days


def referencia_para_anio(year: int) -> date:
    """1 de enero del año del ciclo — la fecha de proyección del legacy."""
    return date(year, 1, 1)
