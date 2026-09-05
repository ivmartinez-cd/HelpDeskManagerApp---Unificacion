"""Casos de uso de escritura de la Tabla KM — port de POST/PATCH/DELETE /tabla-km."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.errors import TablaKmNoEncontradaError
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository


@dataclass(frozen=True)
class ConfigTablaKmPorts:
    tabla_km: TablaKmRepository


@dataclass(frozen=True)
class TablaKmDatos:
    """Campos editables de una fila de Tabla KM — mismos para alta y edición."""

    prestador_id: UUID
    spst_id: UUID | None
    empresa_nombre: str
    sucursal_nombre: str
    observaciones: str | None
    domicilio_cliente: str | None
    localidad_cliente: str | None
    provincia_cliente: str | None
    kms_recorrido: float
    umbral_viatico: float
    aplica_viatico: bool
    kms_a_facturar: float
    url_maps: str | None


class CreateTablaKm:
    def __init__(self, ports: ConfigTablaKmPorts) -> None:
        self._ports = ports

    async def execute(self, datos: TablaKmDatos) -> TablaKm:
        return await self._ports.tabla_km.create(
            prestador_id=datos.prestador_id,
            spst_id=datos.spst_id,
            empresa_nombre=datos.empresa_nombre,
            sucursal_nombre=datos.sucursal_nombre,
            observaciones=datos.observaciones,
            domicilio_cliente=datos.domicilio_cliente,
            localidad_cliente=datos.localidad_cliente,
            provincia_cliente=datos.provincia_cliente,
            kms_recorrido=datos.kms_recorrido,
            umbral_viatico=datos.umbral_viatico,
            aplica_viatico=datos.aplica_viatico,
            kms_a_facturar=datos.kms_a_facturar,
            url_maps=datos.url_maps,
        )


class UpdateTablaKm:
    def __init__(self, ports: ConfigTablaKmPorts) -> None:
        self._ports = ports

    async def execute(self, tabla_km_id: UUID, datos: TablaKmDatos) -> TablaKm:
        updated = await self._ports.tabla_km.update(
            tabla_km_id,
            prestador_id=datos.prestador_id,
            spst_id=datos.spst_id,
            empresa_nombre=datos.empresa_nombre,
            sucursal_nombre=datos.sucursal_nombre,
            observaciones=datos.observaciones,
            domicilio_cliente=datos.domicilio_cliente,
            localidad_cliente=datos.localidad_cliente,
            provincia_cliente=datos.provincia_cliente,
            kms_recorrido=datos.kms_recorrido,
            umbral_viatico=datos.umbral_viatico,
            aplica_viatico=datos.aplica_viatico,
            kms_a_facturar=datos.kms_a_facturar,
            url_maps=datos.url_maps,
        )
        if updated is None:
            raise TablaKmNoEncontradaError(tabla_km_id)
        return updated


class DeleteTablaKm:
    def __init__(self, ports: ConfigTablaKmPorts) -> None:
        self._ports = ports

    async def execute(self, tabla_km_id: UUID) -> TablaKm:
        """Devuelve la fila borrada — el caller necesita su `prestador_id` para
        reanalizar las liquidaciones abiertas afectadas."""
        anterior = await self._ports.tabla_km.get_by_id(tabla_km_id)
        if anterior is None or not await self._ports.tabla_km.delete(tabla_km_id):
            raise TablaKmNoEncontradaError(tabla_km_id)
        return anterior


class SetArchivadaTablaKm:
    """Archivar = ocultar de la pantalla una fila sin actividad reciente; no se
    borra y el motor la sigue usando si la sucursal reaparece."""

    def __init__(self, ports: ConfigTablaKmPorts) -> None:
        self._ports = ports

    async def execute(self, tabla_km_id: UUID, *, archivada: bool) -> TablaKm:
        actualizada = await self._ports.tabla_km.update_archivada(tabla_km_id, archivada)
        if actualizada is None:
            raise TablaKmNoEncontradaError(tabla_km_id)
        return actualizada
