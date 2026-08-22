"""Mapeo pedido → `DatosSolicitud` / entidad `Solicitud` y metadata de
auditoría. Sin I/O salvo el feriado en inicio (días pedidos); la validación
y el orden de efectos viven en gestionar_solicitudes."""

import uuid
from datetime import UTC, date, datetime

from src.modules.vacaciones.application.dtos.solicitud_dtos import (
    CrearSolicitudCommand,
    EditarSolicitudCommand,
)
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud, Solicitud
from src.modules.vacaciones.domain.repositories.feriado_repository import FeriadoRepository
from src.modules.vacaciones.domain.services.dias_solicitados import dias_solicitados
from src.modules.vacaciones.domain.services.validador_solicitud import DatosSolicitud


async def preparar_datos(
    feriados: FeriadoRepository,
    empleado: Empleado,
    command: CrearSolicitudCommand | EditarSolicitudCommand,
) -> DatosSolicitud:
    """Días pedidos (feriado en inicio) + año imputado; lo que el validador
    necesita saber del pedido, antes de tocar agenda o saldo."""
    dias = await _calcular_dias(feriados, command.start_date, command.end_date)
    target = command.charged_to_year or command.start_date.year
    return DatosSolicitud(
        empleado=empleado,
        start_date=command.start_date,
        end_date=command.end_date,
        dias=dias,
        target_year=target,
    )


def nueva_solicitud(datos: DatosSolicitud, reason: str | None) -> Solicitud:
    return Solicitud(
        id=uuid.uuid4(),
        empleado_id=datos.empleado.id,
        start_date=datos.start_date,
        end_date=datos.end_date,
        days_requested=datos.dias,
        charged_to_year=datos.target_year,
        reason=reason,
        status=EstadoSolicitud.PENDING,
        created_at=datetime.now(UTC),
    )


def aplicar_edicion(solicitud: Solicitud, datos: DatosSolicitud, reason: str | None) -> None:
    solicitud.start_date = datos.start_date
    solicitud.end_date = datos.end_date
    solicitud.days_requested = datos.dias
    solicitud.charged_to_year = datos.target_year
    solicitud.reason = reason
    solicitud.status = EstadoSolicitud.PENDING


async def _calcular_dias(feriados: FeriadoRepository, start: date, end: date) -> int:
    feriado_en_inicio = await feriados.existe_no_deduce_en(start)
    return dias_solicitados(start, end, feriado_no_deduce_en_inicio=feriado_en_inicio)


def metadata_solicitud(solicitud: Solicitud, empleado: Empleado | None) -> dict[str, object]:
    return {
        "employee": empleado.nombre_completo if empleado else "",
        "startDate": solicitud.start_date.isoformat(),
        "endDate": solicitud.end_date.isoformat(),
        "days": solicitud.days_requested,
    }
