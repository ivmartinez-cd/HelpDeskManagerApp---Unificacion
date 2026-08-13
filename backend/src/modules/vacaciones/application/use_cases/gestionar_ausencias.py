"""Ciclo de vida de las bajas (absence.controller legacy): nacen APPROVED,
valida solape contra bajas del mismo tipo y contra solicitudes de vacaciones
activas; editar/eliminar es del dueño o del admin.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime

from src.modules.vacaciones.application.dtos.ausencia_dtos import (
    CrearAusenciaCommand,
    EditarAusenciaCommand,
)
from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.registro_auditoria import (
    ACCION_CREATE,
    ACCION_DELETE,
    ACCION_UPDATE,
    ENTIDAD_AUSENCIA,
)
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.errors import (
    AusenciaNoEncontradaError,
    SolapamientoAusenciaError,
    SolapamientoConVacacionesError,
)
from src.modules.vacaciones.domain.repositories.auditoria import (
    RegistradorAuditoria,
    RegistradorAuditoriaNulo,
)
from src.modules.vacaciones.domain.repositories.ausencia_repository import (
    AusenciaRepository,
)
from src.modules.vacaciones.domain.repositories.empleado_repository import EmpleadoRepository
from src.modules.vacaciones.domain.repositories.solicitud_repository import (
    RangoSolapado,
    SolicitudRepository,
)
from src.modules.vacaciones.domain.services.reglas_ausencia import (
    dias_de_baja,
    resolver_empleados_destino,
    verificar_puede_cambiar_estado,
    verificar_puede_modificar_ausencia,
)
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.shared.domain.errors import NotFoundError, ValidationError


@dataclass(frozen=True, slots=True)
class AusenciasDependencies:
    ausencias: AusenciaRepository
    empleados: EmpleadoRepository
    solicitudes: SolicitudRepository
    auditoria: RegistradorAuditoria = RegistradorAuditoriaNulo()


async def _validar_solape(
    deps: AusenciasDependencies,
    empleado_id: uuid.UUID,
    tipo: TipoAusencia,
    start: date,
    end: date,
    excluir_ausencia_id: uuid.UUID | None = None,
) -> None:
    if await deps.ausencias.existe_activa_solapada(
        empleado_id, tipo, start, end, excluir_ausencia_id
    ):
        raise SolapamientoAusenciaError()
    vacaciones = await deps.solicitudes.list_activas_solapadas_de_empleados(
        [empleado_id], RangoSolapado(start=start, end=end)
    )
    if vacaciones:
        raise SolapamientoConVacacionesError()


def _metadata(ausencia: Ausencia, empleado_nombre: str) -> dict[str, object]:
    return {
        "employee": empleado_nombre,
        "type": ausencia.tipo.value,
        "startDate": ausencia.start_date.isoformat(),
        "endDate": ausencia.end_date.isoformat(),
        "days": ausencia.days_count,
    }


class CrearAusencias:
    def __init__(self, deps: AusenciasDependencies) -> None:
        self._deps = deps

    async def execute(
        self, command: CrearAusenciaCommand, actor: ActorVacaciones
    ) -> list[Ausencia]:
        destinos = resolver_empleados_destino(actor, command.empleado_ids)
        empleados = await self._deps.empleados.get_by_ids(destinos)
        if len(empleados) != len(set(destinos)):
            raise NotFoundError("Uno o más empleados no fueron encontrados")
        dias = dias_de_baja(command.start_date, command.end_date)
        if dias <= 0:
            raise ValidationError("El rango de fechas no es válido")
        for empleado_id in destinos:
            await _validar_solape(
                self._deps, empleado_id, command.tipo, command.start_date, command.end_date
            )
        creadas = []
        for empleado_id in destinos:
            ausencia = Ausencia(
                id=uuid.uuid4(),
                empleado_id=empleado_id,
                start_date=command.start_date,
                end_date=command.end_date,
                days_count=dias,
                half_day=command.half_day,
                tipo=command.tipo,
                reason=command.reason,
                status=EstadoSolicitud.APPROVED,
                created_at=datetime.now(UTC),
            )
            await self._deps.ausencias.add(ausencia)
            await self._deps.auditoria.registrar(
                ACCION_CREATE,
                ENTIDAD_AUSENCIA,
                str(ausencia.id),
                _metadata(ausencia, empleados[empleado_id].nombre_completo),
            )
            creadas.append(ausencia)
        return creadas


class EditarAusencia:
    def __init__(self, deps: AusenciasDependencies) -> None:
        self._deps = deps

    async def execute(
        self, ausencia_id: uuid.UUID, command: EditarAusenciaCommand, actor: ActorVacaciones
    ) -> Ausencia:
        ausencia = await self._deps.ausencias.get_by_id(ausencia_id)
        if ausencia is None:
            raise AusenciaNoEncontradaError(ausencia_id)
        verificar_puede_modificar_ausencia(actor, ausencia, accion="editar")
        if command.status is not None:
            verificar_puede_cambiar_estado(actor)
        dias = dias_de_baja(command.start_date, command.end_date)
        if dias <= 0:
            raise ValidationError("El rango de fechas no es válido")
        cambia_agenda = (
            command.tipo is not ausencia.tipo
            or command.start_date != ausencia.start_date
            or command.end_date != ausencia.end_date
        )
        if cambia_agenda:
            await _validar_solape(
                self._deps,
                ausencia.empleado_id,
                command.tipo,
                command.start_date,
                command.end_date,
                excluir_ausencia_id=ausencia.id,
            )
        ausencia.start_date = command.start_date
        ausencia.end_date = command.end_date
        ausencia.days_count = dias
        ausencia.half_day = command.half_day
        ausencia.tipo = command.tipo
        ausencia.reason = command.reason
        ausencia.status = command.status or ausencia.status
        await self._deps.ausencias.save(ausencia)
        await self._registrar(ausencia)
        return ausencia

    async def _registrar(self, ausencia: Ausencia) -> None:
        empleado = await self._deps.empleados.get_by_id(ausencia.empleado_id)
        metadata = _metadata(ausencia, empleado.nombre_completo if empleado else "")
        metadata["status"] = ausencia.status.value
        await self._deps.auditoria.registrar(
            ACCION_UPDATE, ENTIDAD_AUSENCIA, str(ausencia.id), metadata
        )


class EliminarAusencia:
    def __init__(self, deps: AusenciasDependencies) -> None:
        self._deps = deps

    async def execute(self, ausencia_id: uuid.UUID, actor: ActorVacaciones) -> None:
        ausencia = await self._deps.ausencias.get_by_id(ausencia_id)
        if ausencia is None:
            raise AusenciaNoEncontradaError(ausencia_id)
        verificar_puede_modificar_ausencia(actor, ausencia, accion="cancelar")
        empleado = await self._deps.empleados.get_by_id(ausencia.empleado_id)
        await self._deps.ausencias.delete(ausencia_id)
        await self._deps.auditoria.registrar(
            ACCION_DELETE,
            ENTIDAD_AUSENCIA,
            str(ausencia.id),
            _metadata(ausencia, empleado.nombre_completo if empleado else ""),
        )
