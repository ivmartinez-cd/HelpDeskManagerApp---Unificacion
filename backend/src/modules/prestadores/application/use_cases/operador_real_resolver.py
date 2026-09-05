"""Operador real de un PST a una fecha: el historial manda (permite
asignaciones programadas a futuro); el puntero `Prestador.operador_id` es
el fallback para PST sin tramo que cubra la fecha (p. ej. cargados por el
sync sin historial)."""

from dataclasses import replace
from datetime import date

from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.repositories.asignacion_historial_repository import (
    AsignacionHistorialRepository,
)


async def con_operador_real_a(
    asignaciones: AsignacionHistorialRepository, prestadores: list[Prestador], fecha: date
) -> list[Prestador]:
    """Copias de los PST con `operador_id` = operador real a `fecha`."""
    vigentes = await asignaciones.list_vigentes_a(fecha)
    return [replace(p, operador_id=vigentes[p.id]) if p.id in vigentes else p for p in prestadores]
