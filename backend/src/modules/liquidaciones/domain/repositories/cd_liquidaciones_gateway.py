"""Puerto del SOAP de Canal Directo para liquidaciones de prestadores."""

from typing import Protocol

from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import (
    CdIncidenteRow,
    CdLiquidacion,
)


class CdLiquidacionesGateway(Protocol):
    async def get_liquidaciones(
        self, empresa_cd_id: int, top: int = 200
    ) -> list[CdLiquidacion]:
        """Lista las últimas `top` liquidaciones del prestador identificado por `empresa_cd_id`.

        [] si hay error de red/SOAP (se loguea allá).
        """
        ...

    async def get_incidentes(self, liquidacion_id: int) -> list[CdIncidenteRow]:
        """Detalle de incidentes de una liquidación por su id numérico.

        [] es una respuesta legítima (liquidación sin incidentes). Si hay error de
        red/SOAP, levanta `ExternalServiceError` (se loguea allá) — a diferencia de
        `get_liquidaciones`, acá no puede devolver `[]` en el fallo: el caller usa
        este resultado para reconciliar incidentes existentes, y confundir "no hay"
        con "no se pudo consultar" llevaría a borrarlos.
        """
        ...

    async def set_estado(
        self, liquidacion_ayc_id: int, nuevo_estado: str, usuario: str
    ) -> None:
        """Cambia el estado de la liquidación en wsAyC.

        `nuevo_estado`: constante local (`ESTADO_APROBADA`, `ESTADO_OBSERVADA`,
        etc. de `domain/entities/liquidacion.py`) — el gateway la traduce al id
        numérico que espera el SOAP (ver `domain/services/estados_ayc.py`).
        `usuario`: nombre del operador — se pasa para auditoría en AyC.

        NO tiene try/except: la excepción de zeep (o el KeyError de un
        `nuevo_estado` sin contraparte AyC, ej. "abierta") propaga cruda al
        caller, que la envuelve en LiquidacionAyCOperationError. NUNCA falla en
        silencio.
        """
        ...

    async def void_liquidacion(self, liquidacion_ayc_id: int) -> None:
        """Anula la liquidación en wsAyC (voidLiquidation).

        NO tiene try/except: igual que set_estado, propaga cruda. NUNCA falla en silencio.
        """
        ...
