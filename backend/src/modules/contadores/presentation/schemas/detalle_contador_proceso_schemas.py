from datetime import date

from pydantic import BaseModel, ConfigDict

from src.modules.contadores.domain.ports.detalle_contador_proceso_port import (
    DetalleContadorProceso,
)


class DetalleContadorRowSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    empresa: str
    sucursal: str
    sector: str | None
    modelo: str
    serie: str
    nombre_clase: str | None
    fecha_toma_anterior: date | None
    contador_anterior: int
    fecha_toma_actual: date | None
    contador_actual: int
    impresiones_reales: float
    estado_maquina: str | None
    direccion_ip: str | None
    mascara_ip: str | None
    falta_contador: bool
    tipo: str | None


class DetalleContadorProcesoSchema(BaseModel):
    cliente: str
    filas: list[DetalleContadorRowSchema]

    @classmethod
    def from_domain(cls, result: DetalleContadorProceso) -> "DetalleContadorProcesoSchema":
        return cls(
            cliente=result.cliente,
            filas=[DetalleContadorRowSchema.model_validate(f) for f in result.filas],
        )
