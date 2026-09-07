from src.modules.contadores.domain.ports.detalle_contador_proceso_port import (
    DetalleContadorProceso,
    DetalleContadorProcesoPort,
)


class GetDetalleContadorProcesoUseCase:
    def __init__(self, port: DetalleContadorProcesoPort) -> None:
        self._port = port

    async def execute(self, nro_proceso: int) -> DetalleContadorProceso:
        return await self._port.fetch(nro_proceso)
