from datetime import UTC, datetime

from src.modules.preventivos.application.dtos.habilitar_request import (
    DeshabilitarEquipoRequest,
)
from src.modules.preventivos.domain.errors import HabilitacionNoEncontradaError
from src.modules.preventivos.domain.repositories.habilitacion_repository import (
    HabilitacionRepository,
)


class DeshabilitarEquipoUseCase:
    def __init__(self, habilitaciones: HabilitacionRepository) -> None:
        self._habilitaciones = habilitaciones

    async def execute(self, request: DeshabilitarEquipoRequest) -> None:
        desactivada = await self._habilitaciones.desactivar(
            request.siges_maquina_id,
            deshabilitado_por=request.deshabilitado_por_nombre,
            deshabilitado_en=datetime.now(UTC),
        )
        if not desactivada:
            raise HabilitacionNoEncontradaError(request.siges_maquina_id)
