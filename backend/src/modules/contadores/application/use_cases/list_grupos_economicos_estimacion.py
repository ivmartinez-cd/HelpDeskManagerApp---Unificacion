from src.modules.contadores.domain.ports.proceso_estimacion_port import (
    GrupoEconomicoOption,
    ProcesoEstimacionPort,
)


class ListGruposEconomicosEstimacionUseCase:
    def __init__(self, port: ProcesoEstimacionPort) -> None:
        self._port = port

    async def execute(self) -> list[GrupoEconomicoOption]:
        return await self._port.list_grupos_economicos_activos()
