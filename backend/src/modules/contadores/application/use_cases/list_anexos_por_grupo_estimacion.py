from src.modules.contadores.domain.ports.proceso_estimacion_port import (
    AnexoOption,
    ProcesoEstimacionPort,
)


class ListAnexosPorGrupoEstimacionUseCase:
    def __init__(self, port: ProcesoEstimacionPort) -> None:
        self._port = port

    async def execute(self, id_grupo_economico: int) -> list[AnexoOption]:
        return await self._port.list_anexos_por_grupo(id_grupo_economico)
