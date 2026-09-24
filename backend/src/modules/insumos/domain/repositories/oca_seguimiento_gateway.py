"""Puerto de consulta del estado actual de un envío en OCA (solo lectura, sin credenciales)."""

from typing import Protocol

from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca


class OcaSeguimientoGateway(Protocol):
    async def consultar_estado_actual(self, guia: str) -> EstadoOca | None:
        """Último estado del envío, o None si OCA no tiene datos de esa guía.

        Lanza `ExternalServiceError` (o una subclase) ante error de red, HTTP o una
        respuesta que no se puede interpretar."""
        ...
