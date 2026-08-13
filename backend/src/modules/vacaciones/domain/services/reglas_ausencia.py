"""Reglas de acceso y conteo de las bajas (paridad absence.controller legacy):
el jefe/admin registra para cualquier lista de empleados (el legacy no
chequeaba sector en el alta masiva), el empleado solo para sí; editar/eliminar
es del dueño o del admin (el jefe NO edita bajas ajenas), y un no-admin solo
toca bajas PENDING y nunca cambia el estado.
"""

import uuid

from src.modules.vacaciones.domain.entities.ausencia import Ausencia
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.errors import (
    OperacionNoPermitidaError,
    SoloAusenciasPendientesError,
)
from src.modules.vacaciones.domain.services.dias_solicitados import dias_corridos
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.shared.domain.errors import ValidationError

dias_de_baja = dias_corridos
"""Conteo de días de una baja: el legacy usa el mismo calendarDaysBetween
(corridos inclusive + extensión LCT si el fin cae viernes/sábado)."""


def resolver_empleados_destino(
    actor: ActorVacaciones, empleado_ids: list[uuid.UUID]
) -> list[uuid.UUID]:
    if actor.es_admin or actor.es_jefe_de_sector:
        destinos = empleado_ids or ([actor.empleado_id] if actor.empleado_id else [])
    else:
        destinos = [actor.empleado_id] if actor.empleado_id else []
    if not destinos:
        raise ValidationError("No se ha indicado ningún empleado")
    return destinos


def verificar_puede_modificar_ausencia(
    actor: ActorVacaciones, ausencia: Ausencia, *, accion: str
) -> None:
    es_dueno = actor.empleado_id == ausencia.empleado_id
    if not actor.es_admin and not es_dueno:
        raise OperacionNoPermitidaError("No tenés permiso para modificar esta baja")
    if not actor.es_admin and ausencia.status is not EstadoSolicitud.PENDING:
        raise SoloAusenciasPendientesError(accion)


def verificar_puede_cambiar_estado(actor: ActorVacaciones) -> None:
    if not actor.es_admin:
        raise OperacionNoPermitidaError("Sólo un administrador puede cambiar el estado")
