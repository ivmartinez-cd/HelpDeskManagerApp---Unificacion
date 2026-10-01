import uuid
from datetime import UTC, datetime

from src.modules.tareas_varias.application.dtos.solicitud_tv_dto import (
    CrearSolicitudTvAdminRequest,
    SolicitudTvDTO,
)
from src.modules.tareas_varias.application.mappers import solicitud_tv_a_dto
from src.modules.tareas_varias.application.use_cases._autoaprobacion import verificar_no_es_propia
from src.modules.tareas_varias.domain.entities.solicitud_tv import EstadoSolicitudTv, SolicitudTv
from src.modules.tareas_varias.domain.repositories.solicitud_tv_repository import (
    SolicitudTvRepository,
)
from src.modules.tareas_varias.domain.repositories.tecnico_identity_gateway import (
    TecnicoIdentityGateway,
)


class CrearSolicitudTvAdmin:
    """Alta de una solicitud de TV hecha por un supervisor a nombre de un
    técnico. A diferencia de `CrearSolicitudTv` (que nace PENDIENTE y espera
    una decisión posterior), acá la solicitud se aprueba antes de persistir:
    un solo insert que ya queda en estado APROBADA e impacta el Puntaje del
    período al instante."""

    def __init__(self, repo: SolicitudTvRepository, identidades: TecnicoIdentityGateway) -> None:
        self._repo = repo
        self._identidades = identidades

    async def execute(self, request: CrearSolicitudTvAdminRequest) -> SolicitudTvDTO:
        await verificar_no_es_propia(
            self._identidades, request.resuelta_por_user_id, request.id_tecnico
        )
        ahora = datetime.now(UTC)
        solicitud = SolicitudTv(
            id=uuid.uuid4(),
            id_tecnico=request.id_tecnico,
            tecnico=request.tecnico,
            fecha=request.fecha,
            razon_social=request.razon_social,
            sucursal=request.sucursal,
            tarea_realizada=request.tarea_realizada,
            estado=EstadoSolicitudTv.PENDIENTE,
            creado_en=ahora,
        )
        solicitud.aprobar(ahora, request.resuelta_por_email)
        await self._repo.add(solicitud)
        return solicitud_tv_a_dto(solicitud)
