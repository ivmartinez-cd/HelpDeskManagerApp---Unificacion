from datetime import date, datetime

from pydantic import BaseModel

from src.modules.contadores.application.dtos.equipo_sin_real_anotado import (
    EquipoSinRealAnotado,
)
from src.modules.contadores.domain.services.severidad_sin_real import (
    SeveridadSinReal,
    severidad_por_meses,
)


class EquipoSinRealSchema(BaseModel):
    id_maquina: int
    serie: str
    modelo: str
    tecnologia: str | None
    propiedad: str | None
    cliente: str
    sucursal: str
    estado_maquina: str
    observaciones: str
    fecha_ultimo_real: date | None
    fecha_referencia: date
    dias_sin_real: int
    meses_sin_real: int
    nunca_tuvo_real: bool
    im1: int
    im2: int
    im3: int
    imp_prom_3m: int
    severidad: SeveridadSinReal
    operador_nombre: str | None
    operador_color: str | None

    @classmethod
    def from_anotado(cls, anotado: EquipoSinRealAnotado) -> "EquipoSinRealSchema":
        equipo = anotado.equipo
        return cls(
            id_maquina=equipo.id_maquina,
            serie=equipo.serie,
            modelo=equipo.modelo,
            tecnologia=equipo.tecnologia,
            propiedad=equipo.propiedad,
            cliente=equipo.cliente,
            sucursal=equipo.sucursal,
            estado_maquina=equipo.estado_maquina,
            observaciones=equipo.observaciones,
            fecha_ultimo_real=equipo.fecha_ultimo_real,
            fecha_referencia=equipo.fecha_referencia,
            dias_sin_real=equipo.dias_sin_real,
            meses_sin_real=equipo.meses_sin_real,
            nunca_tuvo_real=equipo.nunca_tuvo_real,
            im1=equipo.im1,
            im2=equipo.im2,
            im3=equipo.im3,
            imp_prom_3m=equipo.imp_prom_3m,
            severidad=severidad_por_meses(equipo.meses_sin_real),
            operador_nombre=anotado.operador.nombre if anotado.operador else None,
            operador_color=anotado.operador.color if anotado.operador else None,
        )


class EquiposSinRealResumenSchema(BaseModel):
    total: int
    criticos: int
    altos: int
    medios: int
    bajos: int
    nunca_real: int
    consultado_en: datetime
