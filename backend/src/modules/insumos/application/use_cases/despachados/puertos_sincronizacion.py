"""Puertos y configuración de `SincronizarDespachos` (aparte, para que los pasos de la
corrida los usen sin importar el caso de uso)."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, tzinfo

from src.modules.insumos.domain.repositories.acciones_despacho_repository import (
    CorridasDespachoRepository,
)
from src.modules.insumos.domain.repositories.consulta_despachos_repository import (
    CalendarioFeriados,
)
from src.modules.insumos.domain.repositories.despachos_siges_gateway import (
    DespachosSigesGateway,
)
from src.modules.insumos.domain.repositories.envios_despacho_repository import (
    EnviosDespachoRepository,
    HistorialEstadosRepository,
    RemitosDespachoRepository,
)
from src.modules.insumos.domain.repositories.oca_seguimiento_gateway import (
    OcaSeguimientoGateway,
)
from src.shared.domain.repositories.exclusive_lock import ExclusiveLock


@dataclass(frozen=True, slots=True)
class ConfigSincronizacion:
    dias_ventana: int
    """Días hacia atrás de `Fecha_Remito` que se leen de Siges."""
    distribuciones: tuple[int, ...]
    """`Distribucion.Id` de los transportes OCA."""
    dias_sin_movimiento: int
    """Días hábiles sin cambio de `FechaEstado` para pasar a amarillo."""
    pausa_segundos: float
    """Pausa entre dos consultas seguidas a OCA (no después de la última)."""
    zona_horaria: tzinfo
    """La de Argentina: define qué día es "hoy" para las cuentas de días hábiles."""


@dataclass(frozen=True)
class SincronizarDespachosPorts:
    siges: DespachosSigesGateway
    oca: OcaSeguimientoGateway
    envios: EnviosDespachoRepository
    remitos: RemitosDespachoRepository
    historial: HistorialEstadosRepository
    corridas: CorridasDespachoRepository
    feriados: CalendarioFeriados
    candado: ExclusiveLock
    confirmar: Callable[[], Awaitable[None]]
    """Confirma (commit) lo escrito hasta ahí: la corrida confirma después de cada guía."""
    reloj: Callable[[], datetime]
    """Hora actual, aware en UTC."""
    pausar: Callable[[float], Awaitable[None]]
