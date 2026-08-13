"""Cadena de saldos con carry-over, versión iterativa (D6 del plan).

El legacy (`getBalanceForYear`) recursa hacia atrás con caso base
`prevYear >= 2026` y escribe el carry-over calculado en el ciclo durante la
lectura. Acá la misma matemática se resuelve iterando hacia adelante desde
`ANIO_BASE_CARRY_OVER` con carry inicial 0 — equivalencia exacta, sin stack ni
N consultas anidadas. El write-behind del carry_over lo hace el use case con
el resultado de esta función.
"""

from collections.abc import Mapping
from dataclasses import dataclass

ANIO_BASE_CARRY_OVER = 2026
"""Caso base hardcodeado del legacy: ningún año anterior a este aporta carry."""


@dataclass(frozen=True, slots=True)
class ConsumoAnual:
    used: int
    pending: int


@dataclass(frozen=True, slots=True)
class SaldoAnual:
    year: int
    annual: int
    carry_over: int
    used: int
    pending: int
    available: int


@dataclass(frozen=True, slots=True)
class ReglasCarryOver:
    allow_carry_over: bool
    max_carry_over_days: int  # 0 = ilimitado


def calcular_cadena_saldos(
    target_year: int,
    annual_days_por_anio: Mapping[int, int],
    consumo_por_anio: Mapping[int, ConsumoAnual],
    reglas: ReglasCarryOver,
) -> dict[int, SaldoAnual]:
    """Saldos desde el año base hasta `target_year` inclusive.

    `annual_days_por_anio` debe cubrir todos los años del rango (los provee el
    use case a partir de los ciclos ya asegurados).
    """
    inicio = min(ANIO_BASE_CARRY_OVER, target_year)
    saldos: dict[int, SaldoAnual] = {}
    carry_in = 0
    for year in range(inicio, target_year + 1):
        annual = annual_days_por_anio[year]
        consumo = consumo_por_anio.get(year, ConsumoAnual(used=0, pending=0))
        carry = carry_in if reglas.allow_carry_over else 0
        available = annual + carry - consumo.used - consumo.pending
        saldos[year] = SaldoAnual(
            year=year,
            annual=annual,
            carry_over=carry,
            used=consumo.used,
            pending=consumo.pending,
            available=available,
        )
        carry_in = _carry_out(available, reglas)
    return saldos


def _carry_out(available: int, reglas: ReglasCarryOver) -> int:
    """Clamp del legacy: solo arrastra saldo positivo, topeado por
    `max_carry_over_days` cuando es > 0."""
    if not reglas.allow_carry_over or available <= 0:
        return 0
    if reglas.max_carry_over_days > 0:
        return min(reglas.max_carry_over_days, available)
    return available
