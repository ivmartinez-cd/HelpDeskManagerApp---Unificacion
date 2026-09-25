from typing import Protocol

from src.modules.reporte_incidentes.domain.entities.incidente import (
    DetalleIncidente,
    Empresa,
    Incidente,
    Trabajo,
)


class IncidentesGateway(Protocol):
    """Lecturas de wsAyC que usa el reporte. Solo lectura: ninguna operación
    escribe en Canal Directo."""

    async def listar_empresas(self) -> list[Empresa]:
        """Clientes activos (sin restricción de servicio vencida)."""
        ...

    async def incidentes_recientes(self, empresa: Empresa, top: int) -> list[Incidente]:
        """Los `top` incidentes más recientes del cliente, sin enriquecer."""
        ...

    async def trabajos(self, incidente_id: str) -> list[Trabajo]:
        """Bitácora del técnico, en orden cronológico."""
        ...

    async def detalle(self, incidente_id: str) -> DetalleIncidente:
        ...
