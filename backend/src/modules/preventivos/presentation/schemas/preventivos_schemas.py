from datetime import date, datetime

from pydantic import BaseModel, Field

from src.modules.preventivos.application.dtos.equipo_preventivo_anotado import (
    EquipoPreventivoAnotado,
    HabilitacionInfo,
)
from src.modules.preventivos.application.dtos.punto_mapa_preventivo import (
    PuntoMapaPreventivo,
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
            habilitacion=(
                HabilitacionSchema.from_info(anotado.habilitacion)
                if anotado.habilitacion is not None
                else None
            ),
        )


class EquiposPreventivosPage(Page[EquipoPreventivoSchema]):
    """Page + sello de frescura de la caché del gateway ("actualizado hace X")."""

    consultado_en: datetime


class PuntoMapaSchema(BaseModel):
    id_sucursal: int
    cliente: str
    sucursal: str
    zona: str
    latitud: float | None
    longitud: float | None
    ubicado: bool
    cant_maquinas: int
    cant_habilitadas: int
    peor_estado: EstadoPreventivo
    dias_vencido_max: int | None

    @classmethod
    def from_domain(cls, punto: PuntoMapaPreventivo) -> "PuntoMapaSchema":
        return cls(
            id_sucursal=punto.id_sucursal,
            cliente=punto.cliente,
            sucursal=punto.sucursal,
            zona=punto.zona,
            latitud=punto.latitud,
            longitud=punto.longitud,
            ubicado=punto.ubicado,
            cant_maquinas=punto.cant_maquinas,
            cant_habilitadas=punto.cant_habilitadas,
            peor_estado=punto.peor_estado,
            dias_vencido_max=punto.dias_vencido_max,
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
