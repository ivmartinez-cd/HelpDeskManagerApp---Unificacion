"""Aprobar/rechazar una baja PENDING (la que pidió un empleado para sí:
home office, cambio de horario, etc.). Mismo circuito y mismos alcances que
`DecidirSolicitud` (admin todo; jefe solo su sector; nadie se aprueba a sí
mismo). Si se aprueba y el empleado tiene cuenta con franjas de turno en el
rango, devuelve `afecta_turnos` (ADR-025) para el CTA del frontend -- no
toca la grilla: eso exige criterio humano."""

import uuid
from dataclasses import dataclass, field

from src.modules.vacaciones.application.dtos.ausencia_dtos import (
    DecidirAusenciaCommand,
    DecisionAusenciaResultado,
)
from src.modules.vacaciones.application.dtos.solicitud_dtos import AfectaTurnosAviso
from src.modules.vacaciones.domain.entities.aprobacion import Decision
from src.modules.vacaciones.domain.entities.ausencia import Ausencia
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.registro_auditoria import (
    ACCION_APPROVE,
    ACCION_REJECT,
    ENTIDAD_AUSENCIA,
)
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.errors import (
    AusenciaNoEncontradaError,
    EmpleadoNoEncontradoError,
)
from src.modules.vacaciones.domain.repositories.auditoria import (
    RegistradorAuditoria,
    RegistradorAuditoriaNulo,
)
from src.modules.vacaciones.domain.repositories.ausencia_repository import (
    AusenciaRepository,
)
from src.modules.vacaciones.domain.repositories.empleado_repository import EmpleadoRepository
from src.modules.vacaciones.domain.repositories.impacto_turnos_lookup import (
    ImpactoTurnosLookup,
    ImpactoTurnosLookupNulo,
)
from src.modules.vacaciones.domain.services.scoping import (
    DatosSolicitudAjena,
    verificar_puede_decidir,
)
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones


@dataclass(frozen=True, slots=True)
class DecidirAusenciaDependencies:
    ausencias: AusenciaRepository
    empleados: EmpleadoRepository
    auditoria: RegistradorAuditoria = RegistradorAuditoriaNulo()
    impacto_turnos: ImpactoTurnosLookup = field(default_factory=ImpactoTurnosLookupNulo)


class DecidirAusencia:
    def __init__(self, deps: DecidirAusenciaDependencies) -> None:
        self._deps = deps

    async def execute(
        self, ausencia_id: uuid.UUID, command: DecidirAusenciaCommand, actor: ActorVacaciones
    ) -> DecisionAusenciaResultado:
        ausencia = await self._deps.ausencias.get_by_id(ausencia_id)
        if ausencia is None:
            raise AusenciaNoEncontradaError(ausencia_id)
        empleado = await self._deps.empleados.get_by_id(ausencia.empleado_id)
        if empleado is None:
            raise EmpleadoNoEncontradoError(ausencia.empleado_id)
        verificar_puede_decidir(
            actor,
            DatosSolicitudAjena(empleado_id=empleado.id, department_id=empleado.department_id),
        )
        decision = Decision(command.decision)
        ausencia.status = (
            EstadoSolicitud.APPROVED if decision is Decision.APPROVED else EstadoSolicitud.REJECTED
        )
        await self._deps.ausencias.save(ausencia)
        await self._registrar(ausencia, empleado, decision, command.comment)
        return DecisionAusenciaResultado(
            ausencia=ausencia,
            afecta_turnos=await self._impacto_en_turnos(ausencia, empleado, decision),
        )

    async def _registrar(
        self, ausencia: Ausencia, empleado: Empleado, decision: Decision, comment: str | None
    ) -> None:
        await self._deps.auditoria.registrar(
            ACCION_APPROVE if decision is Decision.APPROVED else ACCION_REJECT,
            ENTIDAD_AUSENCIA,
            str(ausencia.id),
            {
                "employee": empleado.nombre_completo,
                "type": ausencia.tipo.value,
                "startDate": ausencia.start_date.isoformat(),
                "endDate": ausencia.end_date.isoformat(),
                "schedule": ausencia.horario_texto,
                "comment": comment,
            },
        )

    async def _impacto_en_turnos(
        self, ausencia: Ausencia, empleado: Empleado, decision: Decision
    ) -> AfectaTurnosAviso | None:
        if decision is not Decision.APPROVED or empleado.user_id is None:
            return None
        afecta = await self._deps.impacto_turnos.tiene_turnos_en(
            empleado.user_id, ausencia.start_date, ausencia.end_date
        )
        if not afecta:
            return None
        return AfectaTurnosAviso(
            user_id=empleado.user_id, desde=ausencia.start_date, hasta=ausencia.end_date
        )
