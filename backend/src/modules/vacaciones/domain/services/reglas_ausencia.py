"""Reglas de acceso y conteo de las bajas (paridad absence.controller legacy):
el jefe/admin registra para cualquier lista de empleados (el legacy no
chequeaba sector en el alta masiva), el empleado solo para sí (pedir para
otro es 403, no se reescribe en silencio como hacía el legacy); editar/eliminar
es del dueño o del admin (el jefe NO edita bajas ajenas), y un no-admin solo
toca bajas PENDING y nunca cambia el estado.
"""

import uuid
from datetime import date, time

from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.errors import (
    OperacionNoPermitidaError,
    SoloAusenciasPendientesError,
)
from src.modules.vacaciones.domain.services.dias_solicitados import dias_corridos
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.shared.domain.errors import ValidationError

_SIN_EXTENSION_LCT = frozenset({TipoAusencia.HOME_OFFICE, TipoAusencia.CAMBIO_HORARIO})
"""Tipos operativos con aprobación de TL (TIPOS_SOLICITABLES): un día puntual
no debe inflarse a fin de semana completo por caer viernes/sábado, a
diferencia de una baja real (decisión 2026-09-03 — antes `dias_de_baja` era
alias directo de `dias_corridos` y aplicaba esa extensión a todos los tipos
por igual, paridad literal con el legacy)."""


def dias_de_baja(tipo: TipoAusencia, start: date, end: date) -> int:
    """Conteo de días de una baja: el legacy usa el mismo calendarDaysBetween
    (corridos inclusive + extensión LCT si el fin cae viernes/sábado) para
    todos los tipos; acá se excluye esa extensión para `_SIN_EXTENSION_LCT`."""
    return dias_corridos(start, end, aplicar_extension_lct=tipo not in _SIN_EXTENSION_LCT)


def resolver_empleados_destino(
    actor: ActorVacaciones, empleado_ids: list[uuid.UUID]
) -> list[uuid.UUID]:
    propio = [actor.empleado_id] if actor.empleado_id else []
    if actor.es_admin or actor.es_jefe_de_sector:
        destinos = empleado_ids or propio
    else:
        if any(e not in propio for e in empleado_ids):
            raise OperacionNoPermitidaError("Solo podés registrar novedades para vos")
        destinos = propio
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


def estado_inicial(actor: ActorVacaciones) -> EstadoSolicitud:
    """Admin/jefe registran hechos → APPROVED. Un empleado pide para sí →
    PENDING, y la decide quien tiene `approve` (decisión del usuario 2026-08-21:
    los operadores pasan siempre por la TL)."""
    if actor.es_admin or actor.es_jefe_de_sector:
        return EstadoSolicitud.APPROVED
    return EstadoSolicitud.PENDING


def validar_horario(tipo: TipoAusencia, hora_desde: time | None, hora_hasta: time | None) -> None:
    """CAMBIO_HORARIO exige un rango horario válido; el resto no lo lleva."""
    if tipo is TipoAusencia.CAMBIO_HORARIO:
        if hora_desde is None or hora_hasta is None:
            raise ValidationError("El cambio de horario necesita hora desde y hora hasta")
        if hora_hasta <= hora_desde:
            raise ValidationError("La hora hasta debe ser posterior a la hora desde")
    elif hora_desde is not None or hora_hasta is not None:
        raise ValidationError("El horario solo aplica a un cambio de horario")
