"""Value objects del resultado de parsear un Excel maestro de PST (un `.xlsx`/`.xls`
con Prestador+SPSTs+Tarifarios+TablaKM embebidos en varias hojas) — ver
`domain/services/importacion_maestro/`."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SpstImportado:
    nombre: str


@dataclass(frozen=True)
class TarifarioImportado:
    tipo_servicio: str
    costo_servicio: float
    costo_km: float
    vigencia_desde: date


@dataclass(frozen=True)
class TablaKmImportada:
    """`spst_nombre` es el texto crudo de la columna Prestador/Base — el use case
    lo resuelve contra los SPST ya creados con `matching.matchear_spst`, acá es
    solo texto. `aplica_viatico`/`kms_a_facturar`/`umbral_viatico` ya vienen
    calculados (regla de negocio en `importacion_maestro/tabla_km.py`, no en el
    use case)."""

    empresa_nombre: str
    sucursal_nombre: str
    domicilio_cliente: str | None
    localidad_cliente: str | None
    provincia_cliente: str | None
    kms_recorrido: float
    aplica_viatico: bool
    kms_a_facturar: float
    umbral_viatico: float
    url_maps: str | None
    spst_nombre: str | None


@dataclass(frozen=True)
class ResultadoImportacionMaestro:
    """`hoja_tabla_km=None` distingue "ninguna hoja del libro matcheó tabla+km" de
    "había una hoja pero no aportó filas nuevas" — sin esto el mensaje de resultado
    no puede explicar por qué `tabla_km` vino vacío."""

    nombre_corto: str
    vigencia: date
    hoja_tabla_km: str | None
    spsts: list[SpstImportado]
    tarifarios: list[TarifarioImportado]
    tabla_km: list[TablaKmImportada]
