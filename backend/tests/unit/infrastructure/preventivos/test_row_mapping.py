from datetime import date, datetime
from types import SimpleNamespace
from typing import Any

from src.modules.preventivos.infrastructure.siges.row_mapping import (
    map_equipo_row,
    map_zona_row,
)


def _row(**overrides: Any) -> SimpleNamespace:
    """Fila como la devuelve pyodbc para PARQUE_ZONA_SQL (acceso por atributo,
    alias de columna de la consulta, tipos crudos del driver)."""
    base: dict[str, Any] = {
        "id_maquina": 4321,
        "serie": "XYZ123   ",
        "modelo": "MFP Mono Samsung  ",
        "cliente": "Cliente SA",
        "sucursal": "Casa Central",
        "zona": "SUR ",
        "frecuencia_dias": 180,
        "fecha_ultimo_preventivo": datetime(2026, 5, 3, 10, 15),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_mapea_una_fila_completa_recortando_char_fijos() -> None:
    equipo = map_equipo_row(_row())

    assert equipo.id_maquina == 4321
    assert equipo.serie == "XYZ123"
    assert equipo.modelo == "MFP Mono Samsung"
    assert equipo.cliente == "Cliente SA"
    assert equipo.sucursal == "Casa Central"
    assert equipo.zona == "SUR"
    assert equipo.frecuencia_dias == 180


def test_fecha_ultimo_preventivo_pierde_la_hora() -> None:
    assert map_equipo_row(_row()).fecha_ultimo_preventivo == date(2026, 5, 3)


def test_campos_null_no_rompen_el_mapeo() -> None:
    equipo = map_equipo_row(
        _row(
            serie=None,
            modelo=None,
            cliente=None,
            frecuencia_dias=None,
            fecha_ultimo_preventivo=None,
        )
    )

    assert equipo.serie == ""
    assert equipo.modelo == ""
    assert equipo.cliente == ""
    assert equipo.frecuencia_dias is None
    assert equipo.fecha_ultimo_preventivo is None


def test_frecuencia_cero_se_conserva_para_que_el_dominio_decida() -> None:
    assert map_equipo_row(_row(frecuencia_dias=0)).frecuencia_dias == 0


def test_mapea_fila_de_zona() -> None:
    zona = map_zona_row(SimpleNamespace(zona="NORTE  ", maquinas_activas=57))

    assert zona.zona == "NORTE"
    assert zona.maquinas_activas == 57


def test_zona_nula_queda_vacia() -> None:
    assert map_zona_row(SimpleNamespace(zona=None, maquinas_activas=0)).zona == ""
