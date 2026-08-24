from types import SimpleNamespace
from typing import Any

from src.modules.bono_tecnicos.infrastructure.mercurio.incidentes_row_mapping import map_row


def _row(**overrides: Any) -> SimpleNamespace:
    base: dict[str, Any] = {
        "IdIncidente": 834176,
        "Categoria": "Correctivo",
        "Cliente": "Aerolineas Argentinas",
        "Sucursal": "EZE - Hangares",
        "NroSerie": "ZDBXBJCH1000C2D",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_mapea_una_fila() -> None:
    incidente = map_row(_row())

    assert incidente.id_incidente == 834176
    assert incidente.categoria == "Correctivo"
    assert incidente.cliente == "Aerolineas Argentinas"
    assert incidente.sucursal == "EZE - Hangares"
    assert incidente.nro_serie == "ZDBXBJCH1000C2D"


def test_campos_null_no_rompen_el_mapeo() -> None:
    incidente = map_row(_row(Cliente=None, Sucursal=None, NroSerie=None))

    assert incidente.cliente == ""
    assert incidente.sucursal == ""
    assert incidente.nro_serie == ""


def test_recorta_espacios_de_los_char_fijos() -> None:
    assert map_row(_row(NroSerie="ZDBXBJCH1000C2D   ")).nro_serie == "ZDBXBJCH1000C2D"
