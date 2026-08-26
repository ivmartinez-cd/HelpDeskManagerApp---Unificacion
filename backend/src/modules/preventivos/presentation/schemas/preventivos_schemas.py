from datetime import date, datetime

from pydantic import BaseModel, Field

from src.modules.preventivos.application.dtos.equipo_preventivo_anotado import (
    EquipoPreventivoAnotado,
    HabilitacionInfo,
)
from src.modules.preventivos.application.dtos.punto_mapa_preventivo import (
    ConteoEstado,
    PuntoMapaPreventivo,
)
from src.modules.preventivos.domain.entities.sucursal_coordenadas import (
    GeocodificarResultado,
)
from src.modules.preventivos.domain.entities.zona_parque import ZonaParque
from src.modules.preventivos.domain.value_objects.vencimiento_preventivo import (
    EstadoPreventivo,
)
from src.shared.presentation.schemas.pagination import Page


class HabilitacionSchema(BaseModel):
    habilitado_por: str
    habilitado_en: datetime
    nota: str | None

    @classmethod
    def from_info(cls, info: HabilitacionInfo) -> "HabilitacionSchema":
        return cls(
            habilitado_por=info.habilitado_por,
            habilitado_en=info.habilitado_en,
            nota=info.nota,
        )


class EquipoPreventivoSchema(BaseModel):
    id_maquina: int
    serie: str
    modelo: str
    cliente: str
    sucursal: str
    zona: str
    frecuencia_dias: int | None
    fecha_ultimo_preventivo: date | None
    proximo_vencimiento: date | None
    estado: EstadoPreventivo
    dias_vencido: int | None
    fecha_tentativa: date | None
    habilitacion: HabilitacionSchema | None

    @classmethod
    def from_anotado(cls, anotado: EquipoPreventivoAnotado) -> "EquipoPreventivoSchema":
        equipo = anotado.equipo
        return cls(
            id_maquina=equipo.id_maquina,
            serie=equipo.serie,
            modelo=equipo.modelo,
            cliente=equipo.cliente,
            sucursal=equipo.sucursal,
            zona=equipo.zona,
            frecuencia_dias=equipo.frecuencia_dias,
            fecha_ultimo_preventivo=equipo.fecha_ultimo_preventivo,
            proximo_vencimiento=anotado.proximo_vencimiento,
            estado=anotado.estado,
            dias_vencido=anotado.dias_vencido,
            fecha_tentativa=anotado.fecha_tentativa,
            habilitacion=_habilitacion_schema(anotado.habilitacion),
        )


def _habilitacion_schema(info: HabilitacionInfo | None) -> HabilitacionSchema | None:
    return HabilitacionSchema.from_info(info) if info is not None else None


class EquiposPreventivosPage(Page[EquipoPreventivoSchema]):
    """Page + sello de frescura de la caché del gateway ("actualizado hace X")."""

    consultado_en: datetime


class ConteoEstadoSchema(BaseModel):
    estado: EstadoPreventivo
    cantidad: int

    @classmethod
    def from_domain(cls, conteo: ConteoEstado) -> "ConteoEstadoSchema":
        return cls(estado=conteo.estado, cantidad=conteo.cantidad)


class PuntoMapaSchema(BaseModel):
    id_sucursal: int
    cliente: str
    sucursal: str
    zona: str
    domicilio: str
    latitud: float | None
    longitud: float | None
    ubicado: bool
    cant_maquinas: int
    cant_habilitadas: int
    peor_estado: EstadoPreventivo
    fecha_vencido_min: date | None
    fecha_tentativa_min: date | None
    distribucion: list[ConteoEstadoSchema]

    @classmethod
    def from_domain(cls, punto: PuntoMapaPreventivo) -> "PuntoMapaSchema":
        return cls(
            id_sucursal=punto.id_sucursal,
            cliente=punto.cliente,
            sucursal=punto.sucursal,
            zona=punto.zona,
            domicilio=punto.domicilio,
            latitud=punto.latitud,
            longitud=punto.longitud,
            ubicado=punto.ubicado,
            cant_maquinas=punto.cant_maquinas,
            cant_habilitadas=punto.cant_habilitadas,
            peor_estado=punto.peor_estado,
            fecha_vencido_min=punto.fecha_vencido_min,
            fecha_tentativa_min=punto.fecha_tentativa_min,
            distribucion=[ConteoEstadoSchema.from_domain(c) for c in punto.distribucion],
        )


class PuntosMapaPage(Page[PuntoMapaSchema]):
    """Page + sello de frescura + cuánto de lo filtrado no tiene una
    coordenada usable (para que la UI lo avise, no lo esconda)."""

    consultado_en: datetime
    sin_ubicar: int


class ZonaSchema(BaseModel):
    zona: str
    maquinas_activas: int

    @classmethod
    def from_domain(cls, zona: ZonaParque) -> "ZonaSchema":
        return cls(zona=zona.zona, maquinas_activas=zona.maquinas_activas)


class HabilitarEquipoBody(BaseModel):
    nota: str | None = Field(default=None, max_length=300)


class CorregirCoordenadaBody(BaseModel):
    latitud: float
    longitud: float
    nota: str | None = Field(default=None, max_length=300)


class GeocodificarResultadoSchema(BaseModel):
    resueltas: int
    ambiguas: int
    sin_resultados: int
    sin_direccion: int
    reconciliadas: int

    @classmethod
    def from_domain(cls, resultado: GeocodificarResultado) -> "GeocodificarResultadoSchema":
        return cls(
            resueltas=resultado.resueltas,
            ambiguas=resultado.ambiguas,
            sin_resultados=resultado.sin_resultados,
            sin_direccion=resultado.sin_direccion,
            reconciliadas=resultado.reconciliadas,
        )
