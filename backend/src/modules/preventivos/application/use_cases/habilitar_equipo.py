import uuid
from datetime import UTC, datetime

from src.modules.preventivos.application.dtos.equipo_preventivo_anotado import (
    HabilitacionInfo,
)
from src.modules.preventivos.application.dtos.habilitar_request import (
    HabilitarEquipoRequest,
)
from src.modules.preventivos.domain.entities.habilitacion_preventivo import (
    HabilitacionPreventivo,
)
from src.modules.preventivos.domain.errors import HabilitacionYaActivaError
from src.modules.preventivos.domain.repositories.habilitacion_repository import (
    HabilitacionRepository,
)


class HabilitarEquipoUseCase:
    """Marca local, sin escribir nada en Gestión/Siges (alcance v1 del módulo).
    No valida la máquina contra Siges a propósito: los ids llegan del listado
    de la misma pantalla y validar acá costaría una pasada extra por MERCURIO
    en cada toggle."""

    def __init__(self, habilitaciones: HabilitacionRepository) -> None:
        self._habilitaciones = habilitaciones

    async def execute(self, request: HabilitarEquipoRequest) -> HabilitacionInfo:
        existente = await self._habilitaciones.get_activa(request.siges_maquina_id)
        if existente is not None:
            raise HabilitacionYaActivaError(request.siges_maquina_id)
        nota = request.nota.strip() if request.nota and request.nota.strip() else None
        habilitacion = HabilitacionPreventivo(
            id=uuid.uuid4(),
            siges_maquina_id=request.siges_maquina_id,
            habilitado_por_user_id=request.habilitado_por_user_id,
            habilitado_por_nombre=request.habilitado_por_nombre,
            habilitado_en=datetime.now(UTC),
            nota=nota,
            activa=True,
            deshabilitado_en=None,
            deshabilitado_por=None,
        )
        await self._habilitaciones.create(habilitacion)
        return HabilitacionInfo(
            habilitado_por=habilitacion.habilitado_por_nombre,
            habilitado_en=habilitacion.habilitado_en,
            nota=habilitacion.nota,
        )
