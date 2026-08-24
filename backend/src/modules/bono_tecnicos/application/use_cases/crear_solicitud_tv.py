import uuid
from datetime import UTC, datetime

from src.modules.bono_tecnicos.application.dtos.solicitud_tv_dto import (
    CrearSolicitudTvRequest,
    SolicitudTvDTO,
)
from src.modules.bono_tecnicos.application.mappers import solicitud_tv_a_dto
from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv, SolicitudTv
from src.modules.bono_tecnicos.domain.repositories.solicitud_tv_repository import (
    SolicitudTvRepository,
)


class CrearSolicitudTv:
    """Alta de una solicitud de TV — reemplaza la fila que el Google Form
    agregaba al Sheet. Queda PENDIENTE hasta que un supervisor la decida
    (`DecidirSolicitudTv`); no impacta el Puntaje hasta ser APROBADA."""

    def __init__(self, repo: SolicitudTvRepository) -> None:
        self._repo = repo

    async def execute(self, request: CrearSolicitudTvRequest) -> SolicitudTvDTO:
        solicitud = SolicitudTv(
            id=uuid.uuid4(),
            id_tecnico=request.id_tecnico,
            tecnico=request.tecnico,
            fecha=request.fecha,
            razon_social=request.razon_social,
            sucursal=request.sucursal,
            tarea_realizada=request.tarea_realizada,
            estado=EstadoSolicitudTv.PENDIENTE,
            creado_en=datetime.now(UTC),
        )
        await self._repo.add(solicitud)
        return solicitud_tv_a_dto(solicitud)
