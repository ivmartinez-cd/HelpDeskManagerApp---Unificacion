from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ConversacionPendienteDto:
    wa_id: str
    nombre: str
    operador_nombre: str | None
    operador_email: str | None
    sin_asignar: bool
    esperando_desde: datetime
    minutos_esperando: int
    ultimo_mensaje_cliente_at: datetime | None
    ultimo_texto_cliente: str


@dataclass(frozen=True, slots=True)
class OperadorPendientesDto:
    operador: str
    """Nombre del operador, o "Sin asignar"."""
    cantidad: int


@dataclass(frozen=True, slots=True)
class PendientesResumenDto:
    total: int
    sin_asignar: int
    max_minutos_esperando: int
    por_operador: list[OperadorPendientesDto]
    sincronizado_at: datetime | None


@dataclass(frozen=True, slots=True)
class SyncResultadoDto:
    contactos_revisados: int
    esperando: int
    descartados: int
    """Candidatos que no entraron en el tope por ciclo (se revisan en el próximo)."""
