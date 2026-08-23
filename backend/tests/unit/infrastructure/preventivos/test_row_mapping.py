from datetime import date, datetime
from types import SimpleNamespace
from typing import Any

from src.modules.preventivos.infrastructure.siges.row_mapping import (
    map_equipo_row,
    map_sucursal_geocoding_row,
    map_zona_row,
)


def _row(**overrides: Any) -> SimpleNamespace:
    """Fila como la devuelve pyodbc para PARQUE_ZONA_SQL (acceso por atributo,
    alias de columna de la consulta, tipos crudos del driver)."""
    base: dict[str, Any] = {
        "id_maquina": 4321,
        "id_sucursal": 987,
        "serie": "XYZ123   ",
        "modelo": "MFP Mono Samsung  ",
        "cliente": "Cliente SA",
        "sucursal": "Casa Central",
        "zona": "SUR ",
        "frecuencia_dias": 180,
        "fecha_ultimo_preventivo": datetime(2026, 5, 3, 10, 15),
        "latitud": "-34.603722",
        "longitud": "-58.381592",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_mapea_una_fila_completa_recortando_char_fijos() -> None:
    equipo = map_equipo_row(_row())

    assert equipo.id_maquina == 4321
    assert equipo.id_sucursal == 987
    assert equipo.serie == "XYZ123"
    assert equipo.modelo == "MFP Mono Samsung"
    assert equipo.cliente == "Cliente SA"
    assert equipo.sucursal == "Casa Central"
    assert equipo.zona == "SUR"
    assert equipo.frecuencia_dias == 180
    assert equipo.latitud == -34.603722
    assert equipo.longitud == -58.381592


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
            latitud=None,
            longitud=None,
        )
    )

    assert equipo.serie == ""
    assert equipo.modelo == ""
    assert equipo.cliente == ""
    assert equipo.frecuencia_dias is None
    assert equipo.fecha_ultimo_preventivo is None
    assert equipo.latitud is None
    assert equipo.longitud is None


def test_frecuencia_cero_se_conserva_para_que_el_dominio_decida() -> None:
    assert map_equipo_row(_row(frecuencia_dias=0)).frecuencia_dias == 0


def test_coordenada_con_coma_decimal_se_parsea() -> None:
    equipo = map_equipo_row(_row(latitud="-34,6037", longitud="-58,3815"))

    assert equipo.latitud == -34.6037
    assert equipo.longitud == -58.3815


def test_coordenada_vacia_o_no_numerica_queda_none() -> None:
    equipo = map_equipo_row(_row(latitud="", longitud="no es un numero"))

    assert equipo.latitud is None
    assert equipo.longitud is None


def test_mapea_fila_de_zona() -> None:
    zona = map_zona_row(SimpleNamespace(zona="NORTE  ", maquinas_activas=57))

    assert zona.zona == "NORTE"
    assert zona.maquinas_activas == 57


def test_zona_nula_queda_vacia() -> None:
    assert map_zona_row(SimpleNamespace(zona=None, maquinas_activas=0)).zona == ""


def test_mapea_fila_de_sucursal_para_geocoding() -> None:
    fila = SimpleNamespace(
        id_sucursal=42,
        cliente="Cliente SA ",
        sucursal="Casa Central ",
        domicilio="San Isidro 2200 Piso: Dpto: ",
        ciudad="MENDOZA ",
        provincia="Mendoza ",
        latitud="0",
        longitud="0",
    )
    sucursal = map_sucursal_geocoding_row(fila)

    assert sucursal.id_sucursal == 42
    assert sucursal.cliente == "Cliente SA"
    assert sucursal.domicilio == "San Isidro 2200 Piso: Dpto:"
    assert sucursal.ciudad == "MENDOZA"
    assert sucursal.provincia == "Mendoza"
    assert sucursal.latitud == 0.0
    assert sucursal.longitud == 0.0


def test_mapea_fila_de_sucursal_para_geocoding_con_nulos() -> None:
    fila = SimpleNamespace(
        id_sucursal=1,
        cliente=None,
        sucursal=None,
        domicilio=None,
        ciudad=None,
        provincia=None,
        latitud=None,
        longitud=None,
    )
    sucursal = map_sucursal_geocoding_row(fila)

    assert sucursal.cliente == ""
    assert sucursal.domicilio == ""
    assert sucursal.latitud is None
