from datetime import date
from typing import Protocol

from src.modules.contadores.application.dtos.fila_grilla_siges_dto import FilaGrillaSigesDto


class GrillaEstimacionPort(Protocol):
    """Puerto de solo lectura contra Siges — la consulta central del
    Estimador (MODELO_DE_DATOS.md §3.4), una fila por (equipo, clase)."""

    async def fetch_grilla(
        self,
        nro_proceso: int,
        fecha_objetivo: date,
        *,
        fresca: bool = False,
        operador: str | None = None,
    ) -> list[FilaGrillaSigesDto]:
        """`fresca=True` consulta Siges sí o sí (la carga del tablero, como el
        legacy en cada "Cargar"); sin él se reusa la última grilla cargada de
        ese proceso/fecha objetivo (candidatos, recalcular, forzar, export) y
        solo se consulta si todavía no hay ninguna. La grilla recordada es la
        de cada `operador` (v1.7: cada operador trabaja sobre SU lista en
        memoria); `None` = sin operador identificado."""
        ...
