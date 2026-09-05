"""DTO de salida de ReanalizarLiquidacion."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReanalizarLiquidacionResultado:
    total_incidentes: int
    total_alertas: int
