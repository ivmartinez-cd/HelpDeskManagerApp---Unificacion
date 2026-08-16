"""Puerto de resoluciones de coordenadas para sucursales sin pin en Siges."""

from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.sucursal_coordenadas import SucursalCoordenadas


class SucursalCoordenadasRepository(Protocol):
    async def list_by_prestador(self, prestador_id: UUID) -> list[SucursalCoordenadas]: ...

    async def get_by_siges_sucursal_id(
        self, siges_sucursal_id: int
    ) -> SucursalCoordenadas | None: ...

    async def upsert_pendiente(
        self,
        *,
        prestador_id: UUID,
        siges_sucursal_id: int,
        empresa_nombre: str,
        sucursal_nombre: str,
        direccion_normalizada: str | None,
    ) -> SucursalCoordenadas:
        """Crea (o refresca nombres/dirección de) la fila SIN tocar una
        resolución ya guardada — el geocode nunca pisa coordenadas elegidas."""
        ...

    async def resolver(
        self,
        siges_sucursal_id: int,
        *,
        latitud: float,
        longitud: float,
        procedencia: str,
        formatted_address: str | None,
    ) -> SucursalCoordenadas | None: ...
