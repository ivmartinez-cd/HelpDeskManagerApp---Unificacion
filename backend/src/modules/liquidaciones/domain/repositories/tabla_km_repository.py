"""Puerto de kilómetros esperados por par Empresa+Sucursal (tabla_kms)."""

from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm


class TablaKmRepository(Protocol):
    async def list_by_prestador(self, prestador_id: UUID) -> list[TablaKm]:
        """Todas las filas del prestador — el motor de reglas indexa por
        (empresa_nombre, sucursal_nombre) en memoria (ver `_resolucion.py`)."""
        ...

    async def create(
        self,
        *,
        prestador_id: UUID,
        spst_id: UUID | None,
        empresa_nombre: str,
        sucursal_nombre: str,
        observaciones: str | None,
        domicilio_cliente: str | None,
        localidad_cliente: str | None,
        provincia_cliente: str | None,
        kms_recorrido: float,
        umbral_viatico: float,
        aplica_viatico: bool,
        kms_a_facturar: float,
        url_maps: str | None,
    ) -> TablaKm:
        """Genera el `id` (UUID) internamente."""
        ...
