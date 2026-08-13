"""Tests de integración de PandasPrestadorMaestroFileParser contra un .xlsx real
(vía openpyxl+pandas) — el dominio (detección de hojas, extracción de tarifarios/
tabla_km) ya tiene cobertura de caracterización pura en
tests/unit/domain/liquidaciones/test_importacion_maestro_parsing.py; acá se prueba
solo la capa de infraestructura: leer un libro real de varias hojas y convertir
NaN -> None."""

from datetime import date
from io import BytesIO

import openpyxl
import pytest

from src.modules.liquidaciones.domain.errors import ArchivoMaestroInvalidoError
from src.modules.liquidaciones.infrastructure.importers.pandas_prestador_maestro_file_parser import (  # noqa: E501
    PandasPrestadorMaestroFileParser,
)

_GRID_PRINCIPAL = [
    [None, "AGENTE:", "PENTACOM", None],
    [None, None, None, None],
    ["Incidente", "Tipo", "Costo Serv", "Costo Km"],
    ["12345-1", "Correctivo", 1500.0, 100.0],
]


def _xlsx_con_hoja(nombre_hoja: str, grid: list[list[object]]) -> bytes:
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = nombre_hoja
    for fila in grid:
        hoja.append(fila)
    buffer = BytesIO()
    libro.save(buffer)
    return buffer.getvalue()


def test_parse_lee_libro_real_y_extrae_prestador() -> None:
    contenido = _xlsx_con_hoja("ENERO", _GRID_PRINCIPAL)

    resultado = PandasPrestadorMaestroFileParser().parse(contenido, "PENTACOM 202601.xlsx")

    assert resultado.nombre_corto == "PENTACOM"
    assert resultado.vigencia == date(2026, 1, 1)


def test_parse_detects_sheet_by_content_not_by_name() -> None:
    """Bug real del legacy corregido en el port: buscaba la hoja llamada
    literalmente "ENERO" — un archivo de otro mes rompía. El detector nuevo mira
    contenido ("AGENTE:"), no nombre de hoja."""
    contenido = _xlsx_con_hoja("ABRIL", _GRID_PRINCIPAL)

    resultado = PandasPrestadorMaestroFileParser().parse(contenido, "PENTACOM 202604.xlsx")

    assert resultado.nombre_corto == "PENTACOM"


def test_parse_raises_when_no_agente_marker_in_any_sheet() -> None:
    grid_sin_agente = [["Incidente", "Tipo"], ["1", "correctivo"]]
    contenido = _xlsx_con_hoja("Hoja1", grid_sin_agente)

    with pytest.raises(ArchivoMaestroInvalidoError):
        PandasPrestadorMaestroFileParser().parse(contenido, "sin_agente.xlsx")


def test_parse_raises_when_content_is_not_a_valid_workbook() -> None:
    with pytest.raises(ArchivoMaestroInvalidoError):
        PandasPrestadorMaestroFileParser().parse(b"no es un excel", "x.xlsx")
