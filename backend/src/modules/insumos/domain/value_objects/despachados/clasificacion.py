"""Resultado de aplicar las reglas del semáforo a un envío OCA."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class ColorSemaforo(StrEnum):
    VERDE = "verde"
    AMARILLO = "amarillo"
    NARANJA = "naranja"
    ROJO = "rojo"
    GRIS = "gris"
    CERRADO = "cerrado"


@dataclass(frozen=True, slots=True)
class ContextoClasificacion:
    """Lo que las reglas necesitan además del estado de OCA."""

    hoy: date
    """Fecha de hoy en hora Argentina."""
    feriados: frozenset[date]
    """Días no hábiles además de sábados y domingos."""
    dias_sin_movimiento: int = 3
    """Días hábiles sin cambio de `FechaEstado` a partir de los cuales un envío abierto
    pasa a amarillo (también: días de gracia para que OCA registre una guía nueva)."""


@dataclass(frozen=True, slots=True)
class ClasificacionEnvio:
    color: ColorSemaforo
    alerta: bool
    """Requiere acción: naranja (visita fallida o motivo) o rojo (espera en sucursal)."""
    abierto: bool
    """False cuando OCA ya no va a mover el envío (entregado, acuse, devuelto)."""
    fecha_limite: date | None
    """Solo en rojo: último día hábil para retirar en sucursal antes de la devolución."""
    observacion: str
    """Aclaración para la pantalla ("Estado nuevo, revisar", "Sin movimiento hace 4 días
    hábiles", "Esperando ingreso en OCA", "Sin datos en OCA"); "" si no hace falta."""
    estado_desconocido: bool
    """True si el `IdEstado`/texto no está en el catálogo: quien llama lo loguea."""
