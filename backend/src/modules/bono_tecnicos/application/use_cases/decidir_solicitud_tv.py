from datetime import UTC, datetime

from src.modules.bono_tecnicos.application.dtos.solicitud_tv_dto import (
    DecidirSolicitudTvRequest,
    SolicitudTvDTO,
)
from src.modules.bono_tecnicos.application.mappers import solicitud_tv_a_dto
from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv
from src.modules.bono_tecnicos.domain.errors import SolicitudTvNoEncontradaError
from src.modules.bono_tecnicos.domain.repositories.solicitud_tv_repository import (
    SolicitudTvRepository,
)


class DecidirSolicitudTv:
    """Aprobar/rechazar una solicitud de TV. Paridad con vacaciones.
    DecidirSolicitud: no chequea el estado actual, permite re-decidir (ej.
    corregir un rechazo por error) — el Puntaje siempre recalcula en vivo
    contra el estado más reciente, así que no hay riesgo de doble conteo."""

    def __init__(self, repo: SolicitudTvRepository) -> None:
        self._repo = repo

    async def execute(self, request: DecidirSolicitudTvRequest) -> SolicitudTvDTO:
        solicitud = await self._repo.get_by_id(request.solicitud_id)
        if solicitud is None:
            raise SolicitudTvNoEncontradaError(request.solicitud_id)

        ahora = datetime.now(UTC)
        if request.decision == EstadoSolicitudTv.APROBADA.value:
            solicitud.aprobar(ahora, request.resuelta_por_email)
        else:
            solicitud.rechazar(ahora, request.resuelta_por_email, request.motivo)

        await self._repo.save(solicitud)
        return solicitud_tv_a_dto(solicitud)
