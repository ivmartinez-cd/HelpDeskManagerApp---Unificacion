"""DTO de salida de ImportarLiquidacion."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ImportarLiquidacionResultado:
    liquidacion_id: UUID
    total_incidentes: int
    total_alertas: int
