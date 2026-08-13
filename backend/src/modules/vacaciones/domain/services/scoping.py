"""Alcance de datos por actor, server-side (paridad con los filtros por rol
del legacy). El vocabulario: admin (`manage`) ve todo; jefe de sector ve su
sector; empleado ve lo propio. El calendario es la excepción legacy: el
empleado ve el calendario COMPLETO (solo el jefe lo ve acotado a su sector).
"""

import uuid
from dataclasses import dataclass

from src.modules.vacaciones.domain.errors import OperacionNoPermitidaError
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones


@dataclass(frozen=True, slots=True)
class FiltroAlcance:
    """`department_id`/`empleado_id` None y `sin_acceso` False = global."""

    department_id: uuid.UUID | None
    empleado_id: uuid.UUID | None
    sin_acceso: bool


_GLOBAL = FiltroAlcance(department_id=None, empleado_id=None, sin_acceso=False)


def alcance_para_listado(actor: ActorVacaciones) -> FiltroAlcance:
    if actor.es_admin:
        return _GLOBAL
    if actor.sector_gestionado_id is not None:
        return FiltroAlcance(
            department_id=actor.sector_gestionado_id, empleado_id=None, sin_acceso=False
        )
    if actor.empleado_id is not None:
        return FiltroAlcance(department_id=None, empleado_id=actor.empleado_id, sin_acceso=False)
    return FiltroAlcance(department_id=None, empleado_id=None, sin_acceso=True)


def alcance_para_calendario(actor: ActorVacaciones) -> FiltroAlcance:
    if actor.es_jefe_de_sector:
        return FiltroAlcance(
            department_id=actor.sector_gestionado_id, empleado_id=None, sin_acceso=False
        )
    return _GLOBAL


@dataclass(frozen=True, slots=True)
class DatosSolicitudAjena:
    empleado_id: uuid.UUID
    department_id: uuid.UUID


def verificar_puede_ver_solicitud(actor: ActorVacaciones, datos: DatosSolicitudAjena) -> None:
    if actor.es_admin or actor.empleado_id == datos.empleado_id:
        return
    if actor.sector_gestionado_id == datos.department_id:
        return
    raise OperacionNoPermitidaError("No tenés acceso a esta solicitud")


def verificar_puede_decidir(actor: ActorVacaciones, datos: DatosSolicitudAjena) -> None:
    if actor.es_admin:
        return
    if (
        actor.sector_gestionado_id is not None
        and datos.department_id != actor.sector_gestionado_id
    ):
        raise OperacionNoPermitidaError("Solo puedes aprobar solicitudes de tu sector")
    if actor.empleado_id == datos.empleado_id:
        raise OperacionNoPermitidaError("No puedes aprobar tu propia solicitud")


def verificar_puede_ver_solapamientos(
    actor: ActorVacaciones, datos: DatosSolicitudAjena
) -> None:
    if actor.es_admin:
        return
    if (
        actor.sector_gestionado_id is not None
        and datos.department_id != actor.sector_gestionado_id
    ):
        raise OperacionNoPermitidaError("Solo puedes ver solapamientos de tu sector")


def verificar_puede_modificar_solicitud(
    actor: ActorVacaciones, empleado_id_solicitud: uuid.UUID
) -> None:
    """Editar/eliminar: dueño o admin (paridad legacy — el jefe NO edita
    solicitudes ajenas, solo las decide)."""
    if actor.es_admin or actor.empleado_id == empleado_id_solicitud:
        return
    raise OperacionNoPermitidaError("No tenés permiso para modificar esta solicitud")
