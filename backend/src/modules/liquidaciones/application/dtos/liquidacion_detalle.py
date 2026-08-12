"""DTO de salida de GetLiquidacionDetalle."""

from dataclasses import dataclass

from src.modules.liquidaciones.domain.entities.alerta import Alerta
from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
from src.modules.liquidaciones.domain.entities.observacion import Observacion


@dataclass(frozen=True)
class LiquidacionDetalle:
    liquidacion: Liquidacion
    incidentes: list[Incidente]
    alertas: list[Alerta]
    observaciones: list[Observacion]
