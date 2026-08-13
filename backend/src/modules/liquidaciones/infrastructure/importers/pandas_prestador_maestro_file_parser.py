"""Implementación del puerto PrestadorMaestroFileParser con pandas — el archivo
real es un `.xlsx`/`.xls` con varias hojas (`openpyxl` lee `.xlsx`, `xlrd` lee
`.xls` binario). Único punto del módulo que importa pandas para este importador —
todo lo demás (detección de hojas, extracción de filas, dedup en memoria) es
dominio puro sin esta dependencia.

`sheet_name=None` parsea el libro ENTERO (todas las hojas, no solo 2 como el HTML
de liquidaciones) de forma sync dentro del request — trade-off consciente: estos
archivos reales no superan unos pocos cientos de filas por hoja, así que el costo
es aceptable sin justificar mover el parseo a un worker."""

from datetime import date
from io import BytesIO
from typing import Any

import pandas as pd

from src.modules.liquidaciones.domain.errors import ArchivoMaestroInvalidoError
from src.modules.liquidaciones.domain.services.importacion_maestro.constructor import (
    armar_resultado_importacion_maestro,
)
from src.modules.liquidaciones.domain.value_objects.prestador_maestro_importado import (
    ResultadoImportacionMaestro,
)


class PandasPrestadorMaestroFileParser:
    def parse(self, contenido: bytes, nombre_archivo: str) -> ResultadoImportacionMaestro:
        hojas = self._leer_hojas(contenido)
        return armar_resultado_importacion_maestro(hojas, nombre_archivo, date.today())

    def _leer_hojas(self, contenido: bytes) -> dict[str, list[list[Any]]]:
        try:
            libro = pd.read_excel(BytesIO(contenido), sheet_name=None, header=None)
        except Exception as exc:
            raise ArchivoMaestroInvalidoError(f"no se pudo leer el archivo Excel ({exc})") from exc
        # `.astype(object)` antes de `.where` evita que se cuelen tipos numpy
        # (float64, Timestamp) al dominio — no solo NaN→None.
        return {
            nombre: df.astype(object).where(df.notna(), None).values.tolist()
            for nombre, df in libro.items()
        }
