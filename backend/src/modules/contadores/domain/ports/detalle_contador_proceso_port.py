from dataclasses import dataclass
from typing import Protocol

from src.modules.contadores.domain.value_objects.detalle_contador_row import (
    DetalleContadorRow,
)


@dataclass(frozen=True, slots=True)
class DetalleContadorProceso:
    """Reporte completo de un `Nro_Proceso` traído en vivo de Siges —
    equivalente al reporte legacy SSRS "Detalle de contadores por nro de
    proceso" (ver `falta_contador_proceso_query.py` para la investigación
    de origen de datos, compartida por ambos puertos).

    `cliente` es la `empresa` de la primera fila, no una consulta aparte:
    un proceso cae en una sola empresa (ya verificado para
    `FaltaContadorProcesoPort`), y acá cada fila ya trae su propia `empresa`
    del snapshot de `Factura_Contador`."""

    cliente: str
    filas: list[DetalleContadorRow]


class DetalleContadorProcesoPort(Protocol):
    async def fetch(self, nro_proceso: int) -> DetalleContadorProceso:
        """Levanta `ProcesoNoEncontradoError` si el `Nro_Proceso` no existe
        en `Factura_Contador` (distinto de "existe pero sin filas", que no
        es un caso real verificado — todo proceso facturable tiene equipos)."""
        ...
