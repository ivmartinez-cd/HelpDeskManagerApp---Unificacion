from datetime import date
from typing import Protocol

from src.modules.contadores.application.dtos.fila_grilla_siges_dto import FilaGrillaSigesDto


class GrillaEstimacionPort(Protocol):
    """Puerto de solo lectura contra Siges — la consulta central del
    Estimador (MODELO_DE_DATOS.md §3.4), una fila por (equipo, clase)."""

    async def fetch_grilla(
        self, nro_proceso: int, fecha_objetivo: date
    ) -> list[FilaGrillaSigesDto]: ...
