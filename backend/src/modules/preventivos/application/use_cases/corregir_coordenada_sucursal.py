"""Corrección manual de la coordenada de una sucursal desde la UI (2026-08-23):
Siges es de solo lectura para este módulo, así que la única forma de arreglar
un pin mal ubicado hoy es geocodificando de nuevo o editando la DB a mano —
esto le da a un operador (no un desarrollador) una tercera vía. Persiste como
un override más en `preventivos_sucursal_coordenadas`, indistinguible para el
resto del módulo de uno geocodificado (nunca se pisa por una corrida
automática, se libera solo si Siges converge cerca — ver
`GeocodificarSucursalesUseCase`) salvo por los campos de auditoría."""

from datetime import UTC, datetime

from src.modules.preventivos.application.dtos.corregir_coordenada_request import (
    CorregirCoordenadaRequest,
)
from src.modules.preventivos.domain.entities.sucursal_coordenadas import SucursalCoordenadas
from src.modules.preventivos.domain.errors import CoordenadaFueraDeRangoError
from src.modules.preventivos.domain.repositories.sucursal_coordenadas_repository import (
    SucursalCoordenadasRepository,
)
from src.modules.preventivos.domain.services.coordenadas import coordenada_valida

_FORMATTED_ADDRESS_MANUAL = "Corregido manualmente"


class CorregirCoordenadaSucursalUseCase:
    def __init__(self, sucursal_coordenadas: SucursalCoordenadasRepository) -> None:
        self._sucursal_coordenadas = sucursal_coordenadas

    async def execute(self, request: CorregirCoordenadaRequest) -> None:
        if not coordenada_valida(request.latitud, request.longitud):
            raise CoordenadaFueraDeRangoError(request.latitud, request.longitud)
        nota = request.nota.strip() if request.nota and request.nota.strip() else None
        await self._sucursal_coordenadas.upsert(
            SucursalCoordenadas(
                siges_sucursal_id=request.siges_sucursal_id,
                latitud=request.latitud,
                longitud=request.longitud,
                formatted_address=_FORMATTED_ADDRESS_MANUAL,
                fecha_resolucion=datetime.now(UTC),
                corregido_por_user_id=request.corregido_por_user_id,
                corregido_por_nombre=request.corregido_por_nombre,
                nota=nota,
            )
        )
