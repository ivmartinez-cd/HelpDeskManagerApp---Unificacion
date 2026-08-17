from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from src.modules.contadores.application.dtos.anexo_pendiente_con_estado import (
    AnexoPendienteConEstado,
)
from src.modules.contadores.domain.services.periodos_facturacion import EstadoAnexoPendiente


class AnexoPendienteSchema(BaseModel):
    id_anexo: int
    grupo: str | None
    contrato: str | None
    anexo: str
    empresa_admin: str | None
    vendedor: str | None
    moneda: str | None
    moneda_facturacion: str | None
    periodo: str
    fecha_proceso: date
    estado: EstadoAnexoPendiente
    importe_usd: Decimal
    operador_nombre: str | None
    operador_color: str | None

    @classmethod
    def from_anotado(cls, anotado: AnexoPendienteConEstado) -> "AnexoPendienteSchema":
        anexo = anotado.anexo
        return cls(
            id_anexo=anexo.id_anexo,
            grupo=anexo.grupo,
            contrato=anexo.contrato,
            anexo=anexo.anexo,
            empresa_admin=anexo.empresa_admin,
            vendedor=anexo.vendedor,
            moneda=anexo.moneda,
            moneda_facturacion=anexo.moneda_facturacion,
            periodo=anexo.periodo,
            fecha_proceso=anexo.fecha_proceso,
            estado=anotado.estado,
            importe_usd=anexo.importe_usd,
            operador_nombre=anotado.operador.nombre if anotado.operador else None,
            operador_color=anotado.operador.color if anotado.operador else None,
        )


class AnexosPendientesResumenSchema(BaseModel):
    total: int
    en_proceso: int
    demorados: int
    importe_usd_total: Decimal
    periodo_referencia: str
    consultado_en: datetime
