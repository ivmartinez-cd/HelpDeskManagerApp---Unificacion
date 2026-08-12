"""DTO de salida de ReanalizarLiquidacion — mismas 3 claves que devolvía
`ejecutar_motor` del legacy."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReanalizarLiquidacionResultado:
    total_incidentes: int
    total_alertas: int
    total_observaciones: int
