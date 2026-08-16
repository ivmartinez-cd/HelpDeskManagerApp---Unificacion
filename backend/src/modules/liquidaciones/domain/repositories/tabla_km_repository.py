"""Puerto de kilómetros esperados por par Empresa+Sucursal (tabla_kms)."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm


class TablaKmRepository(Protocol):
    async def get_by_id(self, tabla_km_id: UUID) -> TablaKm | None: ...

    async def list_by_prestador(self, prestador_id: UUID) -> list[TablaKm]:
        """Todas las filas del prestador — el motor de reglas indexa por
        (empresa_nombre, sucursal_nombre) en memoria (ver `_resolucion.py`)."""
        ...

    async def set_coordenadas(
        self,
        tabla_km_id: UUID,
        *,
        latitud: float,
        longitud: float,
        coords_origen: str,
        geocode_formatted_address: str | None,
        geocode_fecha: datetime | None,
    ) -> TablaKm | None:
        """Solo el pin destino y su procedencia — no toca km ni viático."""
        ...

    async def update_distancias(
        self,
        tabla_km_id: UUID,
        *,
        kms_ida: float,
        kms_vuelta: float,
        kms_recorrido: float,
        aplica_viatico: bool,
        kms_a_facturar: float,
        url_maps: str | None,
        latitud_destino: float,
        longitud_destino: float,
        coords_origen: str,
    ) -> TablaKm | None:
        """Resultado de un recálculo: km y pin. `umbral_viatico`, `observaciones`
        y el resto de la fila se preservan siempre."""
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
        latitud_destino: float | None = None,
        longitud_destino: float | None = None,
        kms_ida: float | None = None,
        kms_vuelta: float | None = None,
        coords_origen: str | None = None,
        geocode_formatted_address: str | None = None,
        geocode_fecha: datetime | None = None,
    ) -> TablaKm:
        """Genera el `id` (UUID) internamente."""
        ...

    async def update(
        self,
        tabla_km_id: UUID,
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
        latitud_destino: float | None = None,
        longitud_destino: float | None = None,
    ) -> TablaKm | None: ...

    async def delete(self, tabla_km_id: UUID) -> bool: ...
