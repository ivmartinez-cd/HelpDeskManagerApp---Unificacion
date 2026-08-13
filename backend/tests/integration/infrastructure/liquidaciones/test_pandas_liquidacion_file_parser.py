"""Tests de integración de PandasLiquidacionFileParser contra bytes HTML reales
(vía pandas+lxml) — la parte de dominio (mapeo de columnas, construcción de
incidentes) ya tiene cobertura de caracterización pura en
tests/unit/domain/liquidaciones/test_importacion_parsing.py; acá se prueba
solo la capa de infraestructura: leer la tabla HTML real y elegir la correcta."""

import pytest

from src.modules.liquidaciones.domain.errors import ArchivoLiquidacionInvalidoError
from src.modules.liquidaciones.infrastructure.importers.pandas_liquidacion_file_parser import (
    PandasLiquidacionFileParser,
)

_TABLA_INCIDENTES = """
<html><body>
<table>
<tr>
<th>Incidente</th><th>Rubro</th><th>Tipo</th><th>Empresa</th><th>Sucursal</th>
<th>Nro. Serie</th><th>Fecha Cierre</th><th>Costo Serv</th><th>Cant. Km</th>
<th>Costo Km</th><th>Total Viaje</th><th>Costo Total</th><th>P.IT</th>
</tr>
<tr>
<td>12345-1</td><td>Impresoras</td><td>Correctivo</td><td>EMPRESA A</td><td>SUC A</td>
<td>SN1</td><td>2026-01-05</td><td>1500.0</td><td>10.0</td>
<td>100.0</td><td>2500.0</td><td>4000.0</td><td>SI</td>
</tr>
</table>
</body></html>
"""


def _con_tabla_ruido_antes() -> bytes:
    ruido = (
        "<html><body><table><tr><th>A</th><th>B</th></tr>"
        "<tr><td>1</td><td>2</td></tr></table>"
    )
    return (ruido + _TABLA_INCIDENTES + "</body></html>").encode("utf-8")


def test_parse_lee_tabla_incidentes_real_y_construye_resultado() -> None:
    resultado = PandasLiquidacionFileParser().parse(
        _TABLA_INCIDENTES.encode("utf-8"), "liquidacion_3739-6_20260206.xls"
    )

    assert resultado.numero_liquidacion == "3739-6"
    assert len(resultado.incidentes) == 1
    assert resultado.incidentes[0].numero_incidente == "12345-1"
    assert resultado.incidentes[0].empresa_nombre == "EMPRESA A"


def test_parse_elige_la_tabla_con_columna_incidente_entre_varias() -> None:
    resultado = PandasLiquidacionFileParser().parse(
        _con_tabla_ruido_antes(), "liquidacion_9999-1_20260301.xls"
    )

    assert len(resultado.incidentes) == 1
    assert resultado.incidentes[0].numero_incidente == "12345-1"


def test_parse_raises_when_no_tables_in_file() -> None:
    with pytest.raises(ArchivoLiquidacionInvalidoError):
        PandasLiquidacionFileParser().parse(b"<html><body>sin tablas aca</body></html>", "x.xls")


def test_parse_raises_when_content_is_not_html() -> None:
    with pytest.raises(ArchivoLiquidacionInvalidoError):
        PandasLiquidacionFileParser().parse(b"\x00\x01binario-no-html\xff", "x.xls")
