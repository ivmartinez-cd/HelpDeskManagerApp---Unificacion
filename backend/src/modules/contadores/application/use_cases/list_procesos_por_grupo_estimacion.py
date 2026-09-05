from src.modules.contadores.domain.ports.proceso_estimacion_port import (
    ProcesoEstimacionPort,
    ProcesoOption,
)


class ListProcesosPorGrupoEstimacionUseCase:
    def __init__(self, port: ProcesoEstimacionPort) -> None:
        self._port = port

    async def execute(self, id_grupo_economico: int) -> list[ProcesoOption]:
        return await self._port.list_procesos_por_grupo(id_grupo_economico)
