from datetime import datetime
from types import SimpleNamespace
from typing import Any

from src.modules.sla.infrastructure.mercurio.row_mapping import map_row


def _row(**overrides: Any) -> SimpleNamespace:
    """Fila como la devuelve pyodbc (acceso por atributo, nombres de columna
    de la consulta), con los tipos crudos del driver."""
    base: dict[str, Any] = {
        "ID_Incidente": 1234,
        "Fecha_Ingreso": datetime(2026, 8, 3, 10, 0),
        "Tipo": "Correctivo",
        "Estado": "Cerrado",
        "Den_Comercial": "Cliente SA",
        "Sucursal": "Casa Central",
        "Nro_Serie": "XYZ123",
        "Modelo": "HP LaserJet",
        "Tecnico": "CD - Nicolás MON",
        "IdTecnico": 501,
        "REGION": "LOCAL",
        "FechaOperativo": datetime(2026, 8, 4, 15, 30),
        "Periodo": 202608,
        "Tiempo": "26:15",
        "RANGO": "24 a 48",
        "SLA": 24,
        "HorasVencido": "2",
        "Resultado": "Vencido",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_mapea_una_fila_completa() -> None:
    incidente = map_row(_row())

    assert incidente.id_incidente == 1234
    assert incidente.cliente == "Cliente SA"
    assert incidente.tecnico == "CD - Nicolás MON"
    assert incidente.id_tecnico == 501
    assert incidente.region == "LOCAL"
    assert incidente.periodo == 202608
    assert incidente.sla_horas == 24
    assert incidente.horas_vencido == 2
    assert incidente.resultado == "Vencido"
    assert incidente.es_vencido


def test_horas_vencido_llega_como_varchar_y_se_convierte() -> None:
    assert map_row(_row(HorasVencido="17")).horas_vencido == 17
    assert map_row(_row(HorasVencido="0")).horas_vencido == 0


def test_campos_null_no_rompen_el_mapeo() -> None:
    incidente = map_row(
        _row(Tecnico=None, SLA=None, Fecha_Ingreso=None, FechaOperativo=None)
    )

    assert incidente.tecnico == ""
    assert incidente.sla_horas == 0
    assert incidente.fecha_ingreso is None
    assert incidente.fecha_operativo is None


def test_recorta_espacios_de_los_char_fijos() -> None:
    # Los CHAR(n) de SQL Server llegan con padding de espacios.
    assert map_row(_row(Nro_Serie="XYZ123   ")).nro_serie == "XYZ123"
