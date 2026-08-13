"""Puerto del parser del Excel maestro de PST (un `.xlsx`/`.xls` con
Prestador+SPSTs+Tarifarios+TablaKM embebidos en varias hojas) — mismo criterio que
`LiquidacionFileParser`: capacidad externa (pandas) detrás de un Protocol para que el
dominio no dependa de cómo se implementa."""

from typing import Protocol

from src.modules.liquidaciones.domain.value_objects.prestador_maestro_importado import (
    ResultadoImportacionMaestro,
)


class PrestadorMaestroFileParser(Protocol):
    def parse(self, contenido: bytes, nombre_archivo: str) -> ResultadoImportacionMaestro:
        """Lanza `ArchivoMaestroInvalidoError` si el archivo no se puede leer como
        Excel o ninguna hoja tiene una celda "AGENTE:" reconocible."""
        ...
