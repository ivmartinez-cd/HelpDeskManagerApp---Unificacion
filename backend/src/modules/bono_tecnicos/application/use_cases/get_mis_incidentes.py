from src.modules.bono_tecnicos.application.dtos.incidente_bono_dto import (
    GetIncidentesTecnicoRequest,
    GetMisIncidentesRequest,
    IncidenteBonoDTO,
)
from src.modules.bono_tecnicos.application.use_cases.get_incidentes_tecnico import (
    GetIncidentesTecnico,
)
from src.modules.bono_tecnicos.domain.errors import TecnicoNoVinculadoError
from src.modules.bono_tecnicos.domain.repositories.tecnico_identity_gateway import (
    TecnicoIdentityGateway,
)


class GetMisIncidentes:
    """Los incidentes del técnico autenticado en un período — mismo detalle
    que `GetIncidentesTecnico` (el modal de gerencia), pero el `id_tecnico`
    sale del vínculo Empleado↔Siges del propio usuario, nunca del request:
    un técnico solo puede ver lo suyo."""

    def __init__(
        self,
        identity_gateway: TecnicoIdentityGateway,
        get_incidentes_tecnico: GetIncidentesTecnico,
    ) -> None:
        self._identity_gateway = identity_gateway
        self._get_incidentes_tecnico = get_incidentes_tecnico

    async def execute(self, request: GetMisIncidentesRequest) -> list[IncidenteBonoDTO]:
        vinculo = await self._identity_gateway.get_por_usuario(request.user_id)
        if vinculo is None:
            raise TecnicoNoVinculadoError(request.user_id)
        return await self._get_incidentes_tecnico.execute(
            GetIncidentesTecnicoRequest(periodo=request.periodo, id_tecnico=vinculo.id_tecnico)
        )
