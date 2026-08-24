from src.modules.bono_tecnicos.application.dtos.solicitud_tv_dto import (
    CrearSolicitudTvPropiaRequest,
    CrearSolicitudTvRequest,
    SolicitudTvDTO,
)
from src.modules.bono_tecnicos.application.use_cases.crear_solicitud_tv import CrearSolicitudTv
from src.modules.bono_tecnicos.domain.errors import TecnicoNoVinculadoError
from src.modules.bono_tecnicos.domain.repositories.tecnico_identity_gateway import (
    TecnicoIdentityGateway,
)


class CrearSolicitudTvPropia:
    """Igual que `CrearSolicitudTv`, pero resolviendo el técnico desde el
    usuario autenticado (vínculo Empleado↔Siges) en vez de recibirlo del
    cliente — es el endpoint real que usa la pantalla del técnico."""

    def __init__(self, identity_gateway: TecnicoIdentityGateway, crear: CrearSolicitudTv) -> None:
        self._identity_gateway = identity_gateway
        self._crear = crear

    async def execute(self, request: CrearSolicitudTvPropiaRequest) -> SolicitudTvDTO:
        vinculo = await self._identity_gateway.get_por_usuario(request.user_id)
        if vinculo is None:
            raise TecnicoNoVinculadoError(request.user_id)
        return await self._crear.execute(
            CrearSolicitudTvRequest(
                id_tecnico=vinculo.id_tecnico,
                tecnico=vinculo.tecnico,
                fecha=request.fecha,
                razon_social=request.razon_social,
                sucursal=request.sucursal,
                tarea_realizada=request.tarea_realizada,
            )
        )
