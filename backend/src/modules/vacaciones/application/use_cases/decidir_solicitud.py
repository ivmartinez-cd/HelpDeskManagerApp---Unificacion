import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.vacaciones.application.dtos.solicitud_dtos import DecidirSolicitudCommand
from src.modules.vacaciones.domain.entities.aprobacion import Aprobacion, Decision
from src.modules.vacaciones.domain.entities.registro_auditoria import (
    ACCION_APPROVE,
    ACCION_REJECT,
    ENTIDAD_SOLICITUD,
)
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud, Solicitud
from src.modules.vacaciones.domain.errors import (
    EmpleadoNoEncontradoError,
    SolicitudNoEncontradaError,
)
from src.modules.vacaciones.domain.repositories.aprobacion_repository import (
    AprobacionRepository,
)
from src.modules.vacaciones.domain.repositories.auditoria import (
    RegistradorAuditoria,
    RegistradorAuditoriaNulo,
)
from src.modules.vacaciones.domain.repositories.empleado_repository import EmpleadoRepository
from src.modules.vacaciones.domain.repositories.notificador import (
    DecisionNotif,
    Notificador,
)
from src.modules.vacaciones.domain.repositories.solicitud_repository import (
    SolicitudRepository,
)
from src.modules.vacaciones.domain.services.scoping import (
    DatosSolicitudAjena,
    verificar_puede_decidir,
)
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones


@dataclass(frozen=True, slots=True)
class DecidirSolicitudDependencies:
    solicitudes: SolicitudRepository
    empleados: EmpleadoRepository
    aprobaciones: AprobacionRepository
    notificador: Notificador
    auditoria: RegistradorAuditoria = RegistradorAuditoriaNulo()


class DecidirSolicitud:
    """Aprobar/rechazar. Paridad legacy: no chequea el status actual (permite
    re-decidir una solicitud ya decidida) y siempre agrega al historial."""

    def __init__(self, deps: DecidirSolicitudDependencies) -> None:
        self._deps = deps

    async def execute(
        self,
        solicitud_id: uuid.UUID,
        command: DecidirSolicitudCommand,
        actor: ActorVacaciones,
    ) -> Solicitud:
        solicitud = await self._deps.solicitudes.get_by_id(solicitud_id)
        if solicitud is None:
            raise SolicitudNoEncontradaError(solicitud_id)
        empleado = await self._deps.empleados.get_by_id(solicitud.empleado_id)
        if empleado is None:
            raise EmpleadoNoEncontradoError(solicitud.empleado_id)
        verificar_puede_decidir(
            actor,
            DatosSolicitudAjena(
                empleado_id=empleado.id, department_id=empleado.department_id
            ),
        )
        decision = Decision(command.decision)
        solicitud.status = (
            EstadoSolicitud.APPROVED
            if decision is Decision.APPROVED
            else EstadoSolicitud.REJECTED
        )
        await self._deps.solicitudes.save(solicitud)
        await self._deps.aprobaciones.add(
            Aprobacion(
                id=uuid.uuid4(),
                solicitud_id=solicitud.id,
                approver_user_id=actor.user_id,
                decision=decision,
                comment=command.comment,
                created_at=datetime.now(UTC),
            )
        )
        await self._deps.auditoria.registrar(
            ACCION_APPROVE if decision is Decision.APPROVED else ACCION_REJECT,
            ENTIDAD_SOLICITUD,
            str(solicitud.id),
            {
                "employee": empleado.nombre_completo,
                "startDate": solicitud.start_date.isoformat(),
                "endDate": solicitud.end_date.isoformat(),
                "days": solicitud.days_requested,
                "comment": command.comment,
            },
        )
        await self._deps.notificador.notificar_decision(
            DecisionNotif(
                empleado_nombre=empleado.nombre_completo,
                empleado_email=empleado.email,
                aprobada=decision is Decision.APPROVED,
                start_date=solicitud.start_date,
                end_date=solicitud.end_date,
                comment=command.comment,
            )
        )
        return solicitud
