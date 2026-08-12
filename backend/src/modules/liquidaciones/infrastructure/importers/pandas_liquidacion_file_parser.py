"""Implementación del puerto LiquidacionFileParser con pandas + lxml — el archivo
real es una tabla HTML exportada con extensión `.xls` (no un binario XLS real, ni
CSV), mismo formato que parseaba `csv_parser.py` del legacy con `pandas.read_html`.
Único punto del módulo que importa pandas — todo lo demás (mapeo de columnas,
parsing de valores, armado del resultado) es dominio puro sin esta dependencia."""

import logging
from io import BytesIO

import pandas as pd

from src.modules.liquidaciones.domain.errors import ArchivoLiquidacionInvalidoError
from src.modules.liquidaciones.domain.services.importacion.constructor import (
    armar_resultado_importacion,
)
from src.modules.liquidaciones.domain.services.importacion.metadata import mapear_columnas
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    ResultadoImportacion,
)

logger = logging.getLogger(__name__)


class PandasLiquidacionFileParser:
    def parse(self, contenido: bytes, nombre_archivo: str) -> ResultadoImportacion:
        tabla = self._elegir_tabla(self._leer_tablas(contenido))
        tabla = tabla.rename(columns=mapear_columnas(tabla.columns.tolist()))
        filas = [{str(k): v for k, v in fila.items()} for fila in tabla.to_dict("records")]
        return armar_resultado_importacion(nombre_archivo, filas)

    def _leer_tablas(self, contenido: bytes) -> list[pd.DataFrame]:
        # pandas-stubs tipa read_html para ReadBuffer[str], pero en runtime acepta
        # (y necesita) BytesIO — es el mismo patrón que usaba csv_parser.py del
        # legacy contra este formato real.
        try:
            return pd.read_html(BytesIO(contenido), header=0, flavor="lxml")  # type: ignore[arg-type]
        except Exception as exc:
            logger.debug(
                "pandas_liquidacion_file_parser: flavor=lxml falló, reintentando "
                "con el flavor default",
                exc_info=exc,
            )
        try:
            return pd.read_html(BytesIO(contenido), header=0)  # type: ignore[arg-type]
        except Exception as exc:
            raise ArchivoLiquidacionInvalidoError(
                f"no se pudo leer el archivo como tabla HTML ({exc})"
            ) from exc

    def _elegir_tabla(self, tablas: list[pd.DataFrame]) -> pd.DataFrame:
        if not tablas:
            raise ArchivoLiquidacionInvalidoError("no se encontraron tablas en el archivo")
        for tabla in tablas:
            columnas = [str(c).lower() for c in tabla.columns]
            if any("incidente" in c for c in columnas):
                return tabla
        return max(tablas, key=len)
