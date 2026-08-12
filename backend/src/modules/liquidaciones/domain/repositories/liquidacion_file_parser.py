"""Puerto del parser del archivo de preliquidación (HTML-con-extensión-.xls que
exporta el sistema fuente del prestador). Vive en `domain/repositories/` como el
resto de los puertos aunque no sea persistencia — mismo criterio que
`WsAycGateway`/`InsightGateway` en otros módulos: es una capacidad externa que el
dominio necesita sin acoplarse a cómo se implementa (acá: pandas + lxml)."""

from typing import Protocol

from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    ResultadoImportacion,
)


class LiquidacionFileParser(Protocol):
    def parse(self, contenido: bytes, nombre_archivo: str) -> ResultadoImportacion:
        """Lanza `ArchivoLiquidacionInvalidoError` si el archivo no se puede leer
        como tabla o no tiene ninguna columna de incidente reconocible."""
        ...
