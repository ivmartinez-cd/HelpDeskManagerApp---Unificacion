from typing import Protocol

from src.modules.sla.domain.entities.incidente_mesa_ayuda import IncidenteMesaAyuda

# (ID del caso de MDA, ID de la visita de técnico en su sucursal)
ParAvisado = tuple[int, int]


class RegistroAvisosVisita(Protocol):
    """Qué pares caso MDA / visita ya se avisaron — el aviso sale una sola
    vez por par, aunque el job corra cada pocos minutos o se reinicie."""

    async def ya_avisados(self, pares: list[ParAvisado]) -> set[ParAvisado]: ...

    async def registrar(self, pares: list[ParAvisado]) -> None: ...


class NotificadorVisitaSucursal(Protocol):
    """Avisa que hay casos de MDA con una visita de técnico en marcha en la
    misma sucursal. Si falla, lanza: el caso de uso no registra el par y el
    próximo ciclo reintenta."""

    async def avisar(self, incidentes: list[IncidenteMesaAyuda]) -> None: ...
