import uuid
from dataclasses import dataclass
from datetime import date, datetime

from src.modules.contadores.domain.entities.cliente_nuevo import (
    CandidatoClienteNuevo,
    ResumenSigesClienteNuevo,
)


@dataclass(frozen=True, slots=True)
class ClienteNuevoRequest:
    """Input común de alta y edición de una ficha (lo que trae el mail de
    Comercial más lo que decide la TL)."""

    cliente: str
    siges_empresa_id: int | None
    contrato_nro: str | None
    fecha_firma: date | None
    vendedor: str | None
    operador_id: str | None
    implementacion_servicio: str | None
    fecha_estimada_implementacion: date | None
    fecha_estimada_primera_facturacion: date | None
    dia_corte: int | None
    equipos_previstos: int | None
    estado: str
    stc_enviado_el: date | None
    notas: str | None


@dataclass(frozen=True, slots=True)
class ClienteNuevoResult:
    """Ficha + lo que Siges sabe de la empresa (None si la ficha no está
    cruzada con Siges o Siges no respondió) + el aviso `listo_para_stc`."""

    id: uuid.UUID
    cliente: str
    siges_empresa_id: int | None
    contrato_nro: str | None
    fecha_firma: date | None
    vendedor: str | None
    operador_id: str | None
    implementacion_servicio: str | None
    fecha_estimada_implementacion: date | None
    fecha_estimada_primera_facturacion: date | None
    dia_corte: int | None
    equipos_previstos: int | None
    estado: str
    stc_enviado_el: date | None
    notas: str | None
    created_at: datetime
    updated_at: datetime
    siges: ResumenSigesClienteNuevo | None
    listo_para_stc: bool


@dataclass(frozen=True, slots=True)
class CandidatosClientesNuevosResult:
    candidatos: list[CandidatoClienteNuevo]
    firmado_desde: date
