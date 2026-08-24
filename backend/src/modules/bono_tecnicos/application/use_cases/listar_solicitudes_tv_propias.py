from src.modules.bono_tecnicos.application.dtos.solicitud_tv_dto import (
    ListarSolicitudesTvPropiasRequest,
    SolicitudTvDTO,
)
from src.modules.bono_tecnicos.application.mappers import solicitud_tv_a_dto
from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv
from src.modules.bono_tecnicos.domain.errors import TecnicoNoVinculadoError
from src.modules.bono_tecnicos.domain.repositories.solicitud_tv_repository import (
    SolicitudTvRepository,
)
from src.modules.bono_tecnicos.domain.repositories.tecnico_identity_gateway import (
    TecnicoIdentityGateway,
)
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class ListarSolicitudesTvPropias:
    """"Mis solicitudes" del técnico autenticado — mismo filtro por período/
    estado que la cola del supervisor, pero forzado al propio `id_tecnico`
    resuelto del vínculo Empleado↔Siges (nunca al que mande el cliente)."""

    def __init__(
        self, identity_gateway: TecnicoIdentityGateway, repo: SolicitudTvRepository
    ) -> None:
        self._identity_gateway = identity_gateway
        self._repo = repo

    async def execute(self, request: ListarSolicitudesTvPropiasRequest) -> list[SolicitudTvDTO]:
        vinculo = await self._identity_gateway.get_por_usuario(request.user_id)
        if vinculo is None:
            raise TecnicoNoVinculadoError(request.user_id)
        periodo = Periodo(request.periodo)
        estado = EstadoSolicitudTv(request.estado) if request.estado else None
        solicitudes = await self._repo.list_by_periodo(
            periodo, estado=estado, id_tecnico=vinculo.id_tecnico
        )
        return [solicitud_tv_a_dto(s) for s in solicitudes]
