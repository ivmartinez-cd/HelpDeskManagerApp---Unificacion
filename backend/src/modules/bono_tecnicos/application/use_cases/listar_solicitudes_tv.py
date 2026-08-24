from src.modules.bono_tecnicos.application.dtos.solicitud_tv_dto import (
    ListarSolicitudesTvRequest,
    SolicitudTvDTO,
)
from src.modules.bono_tecnicos.application.mappers import solicitud_tv_a_dto
from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv
from src.modules.bono_tecnicos.domain.repositories.solicitud_tv_repository import (
    SolicitudTvRepository,
)
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class ListarSolicitudesTv:
    """Cola de aprobación del supervisor — todas las solicitudes de un
    período, opcionalmente filtradas por estado (ej. solo PENDIENTE) o por
    técnico."""

    def __init__(self, repo: SolicitudTvRepository) -> None:
        self._repo = repo

    async def execute(self, request: ListarSolicitudesTvRequest) -> list[SolicitudTvDTO]:
        periodo = Periodo(request.periodo)
        estado = EstadoSolicitudTv(request.estado) if request.estado else None
        solicitudes = await self._repo.list_by_periodo(
            periodo, estado=estado, id_tecnico=request.id_tecnico
        )
        return [solicitud_tv_a_dto(s) for s in solicitudes]
