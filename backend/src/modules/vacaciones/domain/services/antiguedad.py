"""Días anuales de vacaciones según antigüedad (cycle.service.ts legacy).

La antigüedad se proyecta a una fecha de referencia (el 1/1 del año del ciclo)
con el divisor 365.25 del legacy; los tiers son `min` inclusive / `max`
exclusivo y si la antigüedad supera el último tier se devuelve el último.

Quien ingresó después de la fecha de referencia (antigüedad negativa, el
ingreso del año en curso) cae en el primer tier. El legacy lo dejaba caer al
último y le asignaba el máximo de días a cada ingreso nuevo.
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
    if anios < ordenados[0].min_years:
        return ordenados[0].days
    for tier in ordenados:
        if tier.min_years <= anios < tier.max_years:
            return tier.days
    return ordenados[-1].days


def referencia_para_anio(year: int) -> date:
    """1 de enero del año del ciclo — la fecha de proyección del legacy."""
    return date(year, 1, 1)
