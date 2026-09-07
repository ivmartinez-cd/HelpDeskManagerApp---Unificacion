"""OpenpyxlDetalleContadorWriter: header en negrita, 15 columnas en el
mismo orden de la pantalla, y una fila por `DetalleContadorRow`."""

import io

from openpyxl import load_workbook

from src.modules.contadores.domain.value_objects.detalle_contador_row import (
    DetalleContadorRow,
)
from src.modules.contadores.infrastructure.xlsx.openpyxl_detalle_contador_writer import (
    OpenpyxlDetalleContadorWriter,
)


def _fila() -> DetalleContadorRow:
    return DetalleContadorRow(
        empresa="ISSN",
        sucursal="Botiquin Caviahue",
        sector="Indeterminado",
        modelo="MFP Mono HP 432fdn",
        serie="CNB1R4C0MV",
        nombre_clase="Mono",
        fecha_toma_anterior=None,
        contador_anterior=1,
        fecha_toma_actual=None,
        contador_actual=0,
        impresiones_reales=0.0,
        estado_maquina="Activa en Cliente",
        direccion_ip=None,
        mascara_ip=None,
        falta_contador=True,
        tipo="FALTA CONTADOR Mono",
    )


def test_write_arma_header_y_una_fila_por_registro() -> None:
    contenido = OpenpyxlDetalleContadorWriter().write([_fila(), _fila()])

    wb = load_workbook(io.BytesIO(contenido))
    ws = wb.active
    assert ws is not None
    header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    assert header == [
        "Empresa",
        "Sucursal",
        "Modelo",
        "Serie",
        "Sector",
        "Fecha Toma Ant.",
        "Contador Ant.",
        "Fecha Toma Act.",
        "Contador Act.",
        "Impresiones",
        "Tipo",
        "Clase",
        "Estado Máquina",
        "Dirección IP",
        "Máscara IP",
    ]
    assert next(ws.iter_rows(min_row=1, max_row=1))[0].font.bold is True
    assert ws.max_row == 3
    primera_fila = [c.value for c in next(ws.iter_rows(min_row=2, max_row=2))]
    assert primera_fila[0] == "ISSN"
    assert primera_fila[3] == "CNB1R4C0MV"
    assert primera_fila[10] == "FALTA CONTADOR Mono"


def test_write_sin_filas_deja_solo_el_header() -> None:
    contenido = OpenpyxlDetalleContadorWriter().write([])

    wb = load_workbook(io.BytesIO(contenido))
    ws = wb.active
    assert ws is not None
    assert ws.max_row == 1
