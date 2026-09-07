"""Escritor del reporte ejecutivo XLSX de "Detalle de contadores por
proceso" — mismas 15 columnas que la pantalla (pedido explícito del
usuario, sin resumir para el cliente), armado en memoria: se descarga en la
misma request, a diferencia de las herramientas de `tools_router.py` que sí
necesitan un archivo intermedio en disco."""

import io
from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

from src.modules.contadores.domain.value_objects.detalle_contador_row import (
    DetalleContadorRow,
)

_COLUMNAS: tuple[tuple[str, int], ...] = (
    ("Empresa", 22),
    ("Sucursal", 22),
    ("Modelo", 26),
    ("Serie", 18),
    ("Sector", 20),
    ("Fecha Toma Ant.", 15),
    ("Contador Ant.", 14),
    ("Fecha Toma Act.", 15),
    ("Contador Act.", 14),
    ("Impresiones", 13),
    ("Tipo", 20),
    ("Clase", 10),
    ("Estado Máquina", 18),
    ("Dirección IP", 15),
    ("Máscara IP", 15),
)


class OpenpyxlDetalleContadorWriter:
    def write(self, filas: list[DetalleContadorRow]) -> bytes:
        wb = Workbook()
        ws = wb.active
        assert ws is not None
        ws.title = "Detalle de contadores"
        _encabezado(ws)
        for fila in filas:
            ws.append(_fila_a_excel(fila))
        ws.freeze_panes = "A2"
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()


def _encabezado(ws: Worksheet) -> None:
    ws.append([nombre for nombre, _ in _COLUMNAS])
    for idx, (_, ancho) in enumerate(_COLUMNAS):
        ws.column_dimensions[chr(ord("A") + idx)].width = ancho
    for cell in ws[1]:
        cell.font = Font(bold=True)


def _fila_a_excel(f: DetalleContadorRow) -> list[object]:
    return [
        f.empresa,
        f.sucursal,
        f.modelo,
        f.serie,
        f.sector or "",
        _fecha(f.fecha_toma_anterior),
        f.contador_anterior,
        _fecha(f.fecha_toma_actual),
        f.contador_actual,
        f.impresiones_reales,
        f.tipo or "",
        f.nombre_clase or "",
        f.estado_maquina or "",
        f.direccion_ip or "",
        f.mascara_ip or "",
    ]


def _fecha(valor: date | None) -> str:
    return valor.strftime("%d/%m/%Y") if valor else ""
