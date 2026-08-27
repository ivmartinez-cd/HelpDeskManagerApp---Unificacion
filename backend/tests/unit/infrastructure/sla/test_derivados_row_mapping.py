from datetime import datetime
from types import SimpleNamespace
from typing import Any

from src.modules.sla.infrastructure.mercurio.derivados_row_mapping import map_row


def _row(**overrides: Any) -> SimpleNamespace:
    base: dict[str, Any] = {
        "ID_Incidente": 843579,
        "Fecha_Ingreso": datetime(2026, 8, 18, 10, 9),
        "Tipo": "Correctivo",
        "Estado": "Derivado",
        "Den_Comercial": "EDERSA S.A.",
        "Sucursal": "Casa Central",
        "Nro_Serie": "XYZ123",
        "Modelo": "HP LaserJet",
        "Tecnico": "PST del Interior SA",
        "IdTecnico": 11,
        "DiasDesdeIngreso": 7,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_mapea_una_fila_completa() -> None:
    incidente = map_row(_row())

    assert incidente.id_incidente == 843579
    assert incidente.cliente == "EDERSA S.A."
    assert incidente.tecnico == "PST del Interior SA"
    assert incidente.id_tecnico == 11
    assert incidente.dias_desde_ingreso == 7
    assert not incidente.demorado


def test_campos_null_no_rompen_el_mapeo() -> None:
    incidente = map_row(
        _row(Modelo=None, Sucursal=None, Tecnico=None, IdTecnico=None, Fecha_Ingreso=None)
    )

    assert incidente.modelo == ""
    assert incidente.sucursal == ""
    assert incidente.tecnico == ""
    assert incidente.id_tecnico == 0
    assert incidente.fecha_ingreso is None


def test_recorta_espacios_de_los_char_fijos() -> None:
    assert map_row(_row(Nro_Serie="XYZ123   ")).nro_serie == "XYZ123"


def test_demorado_mas_de_siete_dias() -> None:
    assert not map_row(_row(DiasDesdeIngreso=7)).demorado
    assert map_row(_row(DiasDesdeIngreso=8)).demorado
