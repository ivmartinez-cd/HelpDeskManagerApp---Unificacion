from dataclasses import dataclass
from typing import Protocol

from src.modules.contadores.domain.value_objects.falta_contador_source_row import (
    FaltaContadorSourceRow,
)


@dataclass(frozen=True, slots=True)
class ProcesoFaltaContador:
    """Filas "falta contador" de un `Nro_Proceso` traídas en vivo de Siges,
    más el cliente (derivado — un proceso cae en una sola empresa, ver
    `falta_contador_proceso_query.py`) para nombrar el archivo de salida sin
    pedirlo en el formulario."""

    cliente: str
    filas: list[FaltaContadorSourceRow]


class FaltaContadorProcesoPort(Protocol):
    async def fetch(self, nro_proceso: int) -> ProcesoFaltaContador:
        """Levanta `ProcesoNoEncontradoError` si el `Nro_Proceso` no existe
        en `Factura_Contador` (distinto de "existe pero sin filas
        falta-contador", que es un resultado válido con `filas=[]`)."""
        ...
