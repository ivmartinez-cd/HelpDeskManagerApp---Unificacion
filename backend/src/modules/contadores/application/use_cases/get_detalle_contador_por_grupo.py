from src.modules.contadores.domain.ports.detalle_contador_proceso_port import (
    DetalleContadorProceso,
    DetalleContadorProcesoPort,
)


class GetDetalleContadorPorGrupoUseCase:
    def __init__(self, port: DetalleContadorProcesoPort) -> None:
        self._port = port

    async def execute(self, id_grupo_economico: int) -> DetalleContadorProceso:
        return await self._port.fetch_by_grupo(id_grupo_economico)
