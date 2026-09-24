"""Envío OCA que Despachados sigue: una guía, con lo último que se sabe de ella en OCA, su
clasificación en el semáforo y el cierre manual de la alerta (tabla
`insumos_despacho_envio`)."""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from src.modules.insumos.domain.value_objects.despachados.clasificacion import (
    ClasificacionEnvio,
)
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca


@dataclass(frozen=True, slots=True)
class CierreAlerta:
    """Un operador dio la alerta por atendida. Se reabre si OCA informa otro problema."""

    cerrada_en: datetime
    usuario_id: UUID | None
    """None si el usuario se dio de baja (la FK es ON DELETE SET NULL)."""
    usuario_nombre: str


@dataclass(frozen=True, slots=True)
class ErrorConsulta:
    """Última consulta a OCA fallida; el envío conserva el último estado bueno."""

    mensaje: str
    ocurrido_en: datetime


@dataclass(frozen=True, slots=True)
class EnvioSeguido:
    guia: str
    id_distribucion: int
    fecha_remito: date
    """La del primer remito de la guía en Siges."""
    cliente: str
    sucursal_cliente: str
    clasificacion: ClasificacionEnvio
    estado_oca: EstadoOca | None = None
    """None mientras OCA no registre la guía."""
    consultado_en: datetime | None = None
    """Última consulta a OCA que respondió (con o sin datos)."""
    ultimo_error: ErrorConsulta | None = None
    cierre_alerta: CierreAlerta | None = None

    @property
    def alerta_abierta(self) -> bool:
        return self.clasificacion.alerta and self.cierre_alerta is None
