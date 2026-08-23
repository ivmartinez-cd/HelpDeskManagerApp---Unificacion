from typing import Protocol

from src.modules.preventivos.domain.entities.equipo_preventivo import ParqueZonaSnapshot
from src.modules.preventivos.domain.entities.sucursal_coordenadas import (
    SucursalParaGeocoding,
)
from src.modules.preventivos.domain.entities.zona_parque import ZonaParque


class PreventivosQueryGateway(Protocol):
    """Puerto de consulta a Siges. Devuelve el parque COMPLETO de una zona:
    filtros, búsqueda y orden son del caso de uso, para que una interacción de
    UI no dispare otra pasada por MERCURIO (mismo criterio que
    EquiposSinRealPort de contadores)."""

    async def list_equipos_por_zona(
        self, zona: str, *, force_refresh: bool = False
    ) -> ParqueZonaSnapshot: ...

    async def list_zonas(self) -> list[ZonaParque]: ...

    async def list_sucursales_para_geocoding(self) -> list[SucursalParaGeocoding]:
        """Universo COMPLETO (todas las zonas): la geocodificación es una
        tarea de mantenimiento, no una interacción de UI por zona."""
        ...
