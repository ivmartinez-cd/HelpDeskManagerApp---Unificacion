"""Mapeo de filas de SiGes a `DespachoSiges`: agrupación por remito, incidentes sin
repetir, remitos sin incidente, textos con None/espacios y fechas `smalldatetime`."""

from datetime import date, datetime
from types import SimpleNamespace
from typing import Any

from src.modules.insumos.domain.value_objects.despachados.despacho_siges import (
    DespachoSiges,
    IncidenteInsumo,
)
from src.modules.insumos.infrastructure.siges.mapeo_despachos import mapear_despachos


def _fila(id_remito: int, **cambios: Any) -> SimpleNamespace:
    """Fila como la devuelve pyodbc (acceso por atributo, alias de la consulta)."""
    base: dict[str, Any] = {
        "id_remito": id_remito,
        "numero_remito": 1000 + id_remito,
        "guia": "3867500000001234567",
        "id_distribucion": 3,
        "fecha_remito": datetime(2026, 9, 20, 0, 0),
        "bultos": 2,
        "entrega_a": "Recepción",
        "cliente": "Cliente SA",
        "sucursal_cliente": "Casa Central",
        "numero_incidente": "446207",
        "numero_incidente_cliente": "",
    }
    return SimpleNamespace(**{**base, **cambios})


def test_agrupa_un_remito_con_dos_incidentes_y_filas_repetidas_por_item() -> None:
    filas = [
        _fila(1, numero_incidente="446207", numero_incidente_cliente="OC-1"),
        _fila(1, numero_incidente="446207", numero_incidente_cliente="OC-1"),
        _fila(1, numero_incidente="446300", numero_incidente_cliente=""),
    ]

    [despacho] = mapear_despachos(filas)

    assert despacho.id_remito == 1
    assert despacho.incidentes == (
        IncidenteInsumo(numero="446207", numero_cliente="OC-1"),
        IncidenteInsumo(numero="446300", numero_cliente=""),
    )


def test_remito_sin_incidente_queda_con_la_tupla_vacia() -> None:
    filas = [_fila(7, numero_incidente=None, numero_incidente_cliente=None)]

    [despacho] = mapear_despachos(filas)

    assert despacho.incidentes == ()


def test_incidente_con_numero_en_blanco_se_descarta() -> None:
    filas = [_fila(7, numero_incidente="   "), _fila(7, numero_incidente="446207")]

    [despacho] = mapear_despachos(filas)

    assert despacho.incidentes == (IncidenteInsumo(numero="446207", numero_cliente=""),)


def test_recorta_espacios_y_convierte_none_en_texto_vacio() -> None:
    fila = _fila(
        3,
        guia=" 3867500000001234567 ",
        entrega_a=None,
        cliente="  Cliente SA  ",
        sucursal_cliente=None,
        numero_incidente=" 446207 ",
        numero_incidente_cliente=None,
    )

    [despacho] = mapear_despachos([fila])

    assert despacho.guia == "3867500000001234567"
    assert despacho.entrega_a == ""
    assert despacho.cliente == "Cliente SA"
    assert despacho.sucursal_cliente == ""
    assert despacho.incidentes == (IncidenteInsumo(numero="446207", numero_cliente=""),)


def test_fecha_remito_datetime_pasa_a_date_y_date_se_deja_igual() -> None:
    filas = [
        _fila(1, fecha_remito=datetime(2026, 9, 20, 15, 30)),
        _fila(2, fecha_remito=date(2026, 9, 19)),
    ]

    fechas = [d.fecha_remito for d in mapear_despachos(filas)]

    assert fechas == [date(2026, 9, 20), date(2026, 9, 19)]
    assert all(type(f) is date for f in fechas)


def test_conserva_el_orden_de_aparicion_de_los_remitos() -> None:
    filas = [_fila(9), _fila(4), _fila(9, numero_incidente="500000"), _fila(6)]

    ids = [d.id_remito for d in mapear_despachos(filas)]

    assert ids == [9, 4, 6]


def test_mapea_todos_los_campos_del_remito() -> None:
    [despacho] = mapear_despachos([_fila(5, bultos=None)])

    assert despacho == DespachoSiges(
        id_remito=5,
        numero_remito=1005,
        guia="3867500000001234567",
        id_distribucion=3,
        fecha_remito=date(2026, 9, 20),
        bultos=0,
        cliente="Cliente SA",
        sucursal_cliente="Casa Central",
        entrega_a="Recepción",
        incidentes=(IncidenteInsumo(numero="446207", numero_cliente=""),),
    )


def test_sin_filas_no_hay_despachos() -> None:
    assert mapear_despachos([]) == []
