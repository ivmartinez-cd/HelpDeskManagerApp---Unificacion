from typing import Protocol

from src.modules.contadores.domain.entities.anexo_pendiente import AnexosPendientesSnapshot


class AnexosPendientesPort(Protocol):
    """Puerto de los anexos de Impresión pendientes de cierre.

    Devuelve el universo completo (todos los períodos abiertos dentro de la
    ventana de recencia): el estado EN PROCESO/DEMORADO, la búsqueda y el
    orden son del caso de uso, para que la UI no dispare otra consulta
    contra Siges por cada interacción."""

    async def list_anexos(self, *, force_refresh: bool = False) -> AnexosPendientesSnapshot: ...
