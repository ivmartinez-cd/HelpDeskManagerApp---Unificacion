"""Exports CSV de la configuración de liquidaciones (contraparte de lectura de
`_liq_csv.py`, que tiene los imports — separados para respetar el límite §4 de
300 líneas por archivo). Misma convención de columnas, documentada allá."""

from __future__ import annotations

import csv
import io

from fastapi.responses import StreamingResponse

from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario

_BOM = "﻿"
_CSV_MEDIA = "text/csv; charset=utf-8-sig"


def _csv_response(buf: io.StringIO, filename: str) -> StreamingResponse:
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type=_CSV_MEDIA,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def export_prestadores(rows: list[Prestador]) -> StreamingResponse:
    buf = io.StringIO()
    buf.write(_BOM)
    w = csv.writer(buf)
    w.writerow(["CLAVE", "NOMBRE", "CUIT", "REGION", "ACTIVO"])
    for p in rows:
        activo = "SI" if p.activo else "NO"
        w.writerow([p.nombre_corto, p.nombre, p.cuit or "", p.region or "", activo])
    buf.seek(0)
    return _csv_response(buf, "prestadores.csv")


def export_spsts(rows: list[Spst], prestador_map: dict[str, str]) -> StreamingResponse:
    buf = io.StringIO()
    buf.write(_BOM)
    w = csv.writer(buf)
    w.writerow(["PST_CLAVE", "NOMBRE", "DOMICILIO", "LOCALIDAD", "PROVINCIA", "ZONA", "ACTIVO"])
    for s in rows:
        clave = prestador_map.get(str(s.prestador_id), "")
        w.writerow([
            clave, s.nombre, s.domicilio or "", s.localidad or "",
            s.provincia or "", s.zona or "", "SI" if s.activo else "NO",
        ])
    buf.seek(0)
    return _csv_response(buf, "spsts.csv")


def export_tarifarios(rows: list[Tarifario], prestador_map: dict[str, str]) -> StreamingResponse:
    buf = io.StringIO()
    buf.write(_BOM)
    w = csv.writer(buf)
    w.writerow([
        "PST_CLAVE", "TIPO_SERVICIO", "ZONA", "COSTO_SERVICIO",
        "COSTO_KM", "VIGENCIA_DESDE", "VIGENCIA_HASTA",
    ])
    for t in rows:
        clave = prestador_map.get(str(t.prestador_id), "")
        w.writerow([
            clave, t.tipo_servicio, t.zona or "",
            t.costo_servicio, t.costo_km,
            t.vigencia_desde.isoformat(),
            t.vigencia_hasta.isoformat() if t.vigencia_hasta else "",
        ])
    buf.seek(0)
    return _csv_response(buf, "tarifarios.csv")


def export_tabla_km(rows: list[TablaKm], prestador_map: dict[str, str]) -> StreamingResponse:
    buf = io.StringIO()
    buf.write(_BOM)
    w = csv.writer(buf)
    w.writerow([
        "PST_CLAVE", "EMPRESA", "SUCURSAL", "DOMICILIO", "LOCALIDAD", "PROVINCIA",
        "KMS_RECORRIDO", "KMS_A_FACTURAR", "UMBRAL_VIATICO", "APLICA_VIATICO",
        "URL_MAPS", "OBSERVACIONES",
    ])
    for t in rows:
        clave = prestador_map.get(str(t.prestador_id), "")
        w.writerow([
            clave, t.empresa_nombre, t.sucursal_nombre,
            t.domicilio_cliente or "", t.localidad_cliente or "", t.provincia_cliente or "",
            t.kms_recorrido, t.kms_a_facturar, t.umbral_viatico,
            "SI" if t.aplica_viatico else "NO",
            t.url_maps or "", t.observaciones or "",
        ])
    buf.seek(0)
    return _csv_response(buf, "tabla_km.csv")
