"""Schemas del detalle de una guía de Insumos > Despachados (camelCase, fechas ISO; ver
`despachados_schemas.py`)."""

from datetime import date, datetime

from src.modules.insumos.application.dtos.despachados import DetalleDespacho
from src.modules.insumos.domain.entities.despachados.envio_seguido import (
    CierreAlerta,
    EnvioSeguido,
    ErrorConsulta,
)
from src.modules.insumos.domain.value_objects.despachados.cambio_estado import CambioEstado
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import (
    DespachoSiges,
    IncidenteInsumo,
)
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca
from src.modules.insumos.presentation.schemas.despachados_schemas import AccionOut, CamelOut


class EstadoOcaOut(CamelOut):
    operativa: str
    orden_retiro: str
    sucursal_actual: str
    fecha_estado: date
    estado: str
    id_estado: int | None
    motivo: str
    cantidad_paquetes: int | None

    @classmethod
    def from_estado(cls, estado: EstadoOca) -> "EstadoOcaOut":
        return cls(**{c: getattr(estado, c) for c in cls.model_fields})


class ErrorConsultaOut(CamelOut):
    mensaje: str
    ocurrido_en: datetime

    @classmethod
    def from_error(cls, error: ErrorConsulta | None) -> "ErrorConsultaOut | None":
        if error is None:
            return None
        return cls(mensaje=error.mensaje, ocurrido_en=error.ocurrido_en)


class CierreAlertaOut(CamelOut):
    cerrada_en: datetime
    usuario_nombre: str

    @classmethod
    def from_cierre(cls, cierre: CierreAlerta | None) -> "CierreAlertaOut | None":
        if cierre is None:
            return None
        return cls(cerrada_en=cierre.cerrada_en, usuario_nombre=cierre.usuario_nombre)


class EnvioOut(CamelOut):
    guia: str
    id_distribucion: int
    fecha_remito: date
    cliente: str
    sucursal_cliente: str
    color: ColorSemaforo
    alerta: bool
    """Las reglas piden acción (rojo o naranja), esté o no cerrada la alerta."""
    alerta_abierta: bool
    abierto: bool
    fecha_limite: date | None
    observacion: str
    estado_oca: EstadoOcaOut | None
    consultado_en: datetime | None
    ultimo_error: ErrorConsultaOut | None
    cierre_alerta: CierreAlertaOut | None

    @classmethod
    def from_envio(cls, envio: EnvioSeguido) -> "EnvioOut":
        """Aplana la clasificación; el estado de OCA, el error y el cierre van anidados."""
        clasificacion, estado = envio.clasificacion, envio.estado_oca
        return cls(
            guia=envio.guia,
            id_distribucion=envio.id_distribucion,
            fecha_remito=envio.fecha_remito,
            cliente=envio.cliente,
            sucursal_cliente=envio.sucursal_cliente,
            color=clasificacion.color,
            alerta=clasificacion.alerta,
            alerta_abierta=envio.alerta_abierta,
            abierto=clasificacion.abierto,
            fecha_limite=clasificacion.fecha_limite,
            observacion=clasificacion.observacion,
            estado_oca=None if estado is None else EstadoOcaOut.from_estado(estado),
            consultado_en=envio.consultado_en,
            ultimo_error=ErrorConsultaOut.from_error(envio.ultimo_error),
            cierre_alerta=CierreAlertaOut.from_cierre(envio.cierre_alerta),
        )


class IncidenteOut(CamelOut):
    numero: str
    numero_cliente: str

    @classmethod
    def from_incidente(cls, incidente: IncidenteInsumo) -> "IncidenteOut":
        return cls(numero=incidente.numero, numero_cliente=incidente.numero_cliente)


class RemitoOut(CamelOut):
    id_remito: int
    numero_remito: int
    fecha_remito: date
    id_distribucion: int
    bultos: int
    cliente: str
    sucursal_cliente: str
    entrega_a: str
    incidentes: list[IncidenteOut]

    @classmethod
    def from_despacho(cls, despacho: DespachoSiges) -> "RemitoOut":
        datos = {c: getattr(despacho, c) for c in cls.model_fields if c != "incidentes"}
        incidentes = [IncidenteOut.from_incidente(i) for i in despacho.incidentes]
        return cls(**datos, incidentes=incidentes)


class CambioEstadoOut(CamelOut):
    id_estado: int | None
    estado: str
    motivo: str
    sucursal: str
    fecha_estado: date
    color: ColorSemaforo
    observado_en: datetime

    @classmethod
    def from_cambio(cls, cambio: CambioEstado) -> "CambioEstadoOut":
        return cls(**{c: getattr(cambio, c) for c in cls.model_fields})


class DetalleOut(CamelOut):
    envio: EnvioOut
    dias_habiles_para_limite: int | None
    """Solo en rojo con fecha límite: 0 vence hoy, negativo vencido."""
    remitos: list[RemitoOut]
    """Del más viejo al más nuevo."""
    cambios: list[CambioEstadoOut]
    """Cambios de estado que observó el job, del más reciente al más viejo."""
    acciones: list[AccionOut]
    """De la más reciente a la más vieja."""

    @classmethod
    def from_detalle(cls, detalle: DetalleDespacho) -> "DetalleOut":
        return cls(
            envio=EnvioOut.from_envio(detalle.envio),
            dias_habiles_para_limite=detalle.dias_habiles_para_limite,
            remitos=[RemitoOut.from_despacho(r) for r in detalle.remitos],
            cambios=[CambioEstadoOut.from_cambio(c) for c in detalle.cambios],
            acciones=[AccionOut.from_accion(a) for a in detalle.acciones],
        )
