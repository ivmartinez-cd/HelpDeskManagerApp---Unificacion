"""Mapeo `TablaKmModel` (fila ORM) → `TablaKm` (entidad de dominio), compartido
por las dos mitades de `SqlAlchemyTablaKmRepository` (consultas y escrituras)."""

from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.infrastructure.models.tabla_km_model import TablaKmModel


def to_entity(row: TablaKmModel) -> TablaKm:
    return TablaKm(
        id=row.id,
        prestador_id=row.prestador_id,
        spst_id=row.spst_id,
        empresa_nombre=row.empresa_nombre,
        sucursal_nombre=row.sucursal_nombre,
        observaciones=row.observaciones,
        domicilio_cliente=row.domicilio_cliente,
        localidad_cliente=row.localidad_cliente,
        provincia_cliente=row.provincia_cliente,
        kms_recorrido=row.kms_recorrido,
        umbral_viatico=row.umbral_viatico,
        aplica_viatico=row.aplica_viatico,
        kms_a_facturar=row.kms_a_facturar,
        url_maps=row.url_maps,
        latitud_destino=row.latitud_destino,
        longitud_destino=row.longitud_destino,
        created_at=row.created_at,
        updated_at=row.updated_at,
        kms_ida=row.kms_ida,
        kms_vuelta=row.kms_vuelta,
        coords_origen=row.coords_origen,
        geocode_formatted_address=row.geocode_formatted_address,
        geocode_fecha=row.geocode_fecha,
        siges_sucursal_id=row.siges_sucursal_id,
        id_costo_servicios=row.id_costo_servicios,
        archivada=row.archivada,
    )
