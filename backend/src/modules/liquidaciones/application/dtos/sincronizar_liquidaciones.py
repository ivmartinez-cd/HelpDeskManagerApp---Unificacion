"""DTO de resultado del sync de liquidaciones desde Canal Directo."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SincronizarLiquidacionesResultado:
    creadas: int
    ya_existentes: int
    sin_prestador: int
