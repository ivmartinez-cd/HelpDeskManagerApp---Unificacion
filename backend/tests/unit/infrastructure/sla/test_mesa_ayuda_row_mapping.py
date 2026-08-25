from datetime import datetime
from types import SimpleNamespace
from typing import Any

from src.modules.sla.infrastructure.mercurio.mesa_ayuda_row_mapping import map_row


def _row(**overrides: Any) -> SimpleNamespace:
    base: dict[str, Any] = {
        "ID_Incidente": 843579,
        "Fecha_Ingreso": datetime(2026, 8, 18, 10, 9),
        "Tipo": "Correctivo",
        "Estado": "Demorado",
        "Den_Comercial": "EDERSA S.A.",
        "Sucursal": "Casa Central",
        "Nro_Serie": "XYZ123",
        "Modelo": "HP LaserJet",
        "OperadorLogin": "vipaez",
        "OperadorNombre": "Victor",
        "OperadorApellido": "Paez",
        "DiasTranscurridos": 7,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_mapea_una_fila_completa() -> None:
    incidente = map_row(_row())

    assert incidente.id_incidente == 843579
    assert incidente.cliente == "EDERSA S.A."
    assert incidente.operador_login == "vipaez"
    assert incidente.operador == "Victor Paez"
    assert incidente.dias_transcurridos == 7
    assert not incidente.demorado


def test_operador_sin_match_en_usuarios_web_cae_al_login() -> None:
    incidente = map_row(_row(OperadorNombre=None, OperadorApellido=None))

    assert incidente.operador == "vipaez"


def test_campos_null_no_rompen_el_mapeo() -> None:
    incidente = map_row(
        _row(
            Modelo=None,
            Sucursal=None,
            OperadorLogin=None,
            OperadorNombre=None,
            OperadorApellido=None,
            Fecha_Ingreso=None,
        )
    )

    assert incidente.modelo == ""
    assert incidente.sucursal == ""
    assert incidente.operador_login == ""
    assert incidente.operador == ""
    assert incidente.fecha_ingreso is None


def test_recorta_espacios_de_los_char_fijos() -> None:
    assert map_row(_row(Nro_Serie="XYZ123   ")).nro_serie == "XYZ123"


def test_demorado_mas_de_siete_dias() -> None:
    assert not map_row(_row(DiasTranscurridos=7)).demorado
    assert map_row(_row(DiasTranscurridos=8)).demorado
