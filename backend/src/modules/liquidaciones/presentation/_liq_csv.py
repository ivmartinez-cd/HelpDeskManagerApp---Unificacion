"""Helpers de CSV para los endpoints de configuración de liquidaciones.

Separados del router para mantener config_router.py por debajo de 300 líneas.
Convención de columnas:
  prestadores   → CLAVE, NOMBRE, CUIT, REGION
  spsts         → PST_CLAVE, NOMBRE, DOMICILIO, LOCALIDAD, PROVINCIA, ZONA
  tarifarios    → PST_CLAVE, TIPO_SERVICIO, ZONA, COSTO_SERVICIO, COSTO_KM,
                  VIGENCIA_DESDE, VIGENCIA_HASTA
  tabla_km      → PST_CLAVE, EMPRESA, SUCURSAL, DOMICILIO, LOCALIDAD,
                  PROVINCIA, KMS_RECORRIDO, KMS_A_FACTURAR, UMBRAL_VIATICO,
                  APLICA_VIATICO, URL_MAPS, OBSERVACIONES
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import date

from fastapi import UploadFile
from fastapi.responses import StreamingResponse

from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_spst_repository import (
    SqlAlchemySpstRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (
    SqlAlchemyTablaKmRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tarifario_repository import (
    SqlAlchemyTarifarioRepository,
)

logger = logging.getLogger(__name__)

_BOM = "﻿"
_CSV_MEDIA = "text/csv; charset=utf-8-sig"


def _csv_response(buf: io.StringIO, filename: str) -> StreamingResponse:
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type=_CSV_MEDIA,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _read_csv(file_bytes: bytes) -> list[dict[str, str]]:
    text = file_bytes.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


# ─── Prestadores ─────────────────────────────────────────────────────────────


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


async def import_prestadores(
    file: UploadFile, repo: SqlAlchemyPrestadorRepository
) -> dict[str, int]:
    rows = _read_csv(await file.read())
    created = 0
    for row in rows:
        clave = (row.get("CLAVE") or "").strip().upper()
        nombre = (row.get("NOMBRE") or "").strip()
        if not clave or not nombre:
            continue
        if await repo.get_by_nombre_corto(clave):
            continue
        await repo.create(
            nombre=nombre,
            nombre_corto=clave,
            cuit=(row.get("CUIT") or "").strip() or None,
            region=(row.get("REGION") or "").strip() or None,
        )
        created += 1
    return {"creados": created}


# ─── SPSTs ───────────────────────────────────────────────────────────────────


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


async def import_spsts(
    file: UploadFile,
    repo: SqlAlchemySpstRepository,
    prestador_repo: SqlAlchemyPrestadorRepository,
) -> dict[str, int]:
    rows = _read_csv(await file.read())
    created = 0
    for row in rows:
        pst_clave = (row.get("PST_CLAVE") or "").strip().upper()
        nombre = (row.get("NOMBRE") or "").strip()
        if not pst_clave or not nombre:
            continue
        prestador = await prestador_repo.get_by_nombre_corto(pst_clave)
        if not prestador:
            logger.warning("import_spsts: PST_CLAVE '%s' no encontrada, fila omitida", pst_clave)
            continue
        await repo.create(
            prestador_id=prestador.id,
            nombre=nombre,
            domicilio=(row.get("DOMICILIO") or "").strip() or None,
            localidad=(row.get("LOCALIDAD") or "").strip() or None,
            provincia=(row.get("PROVINCIA") or "").strip() or None,
            zona=(row.get("ZONA") or "").strip() or None,
        )
        created += 1
    return {"creados": created}


# ─── Tarifarios ──────────────────────────────────────────────────────────────


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


def _parse_date(val: str) -> date | None:
    val = val.strip()
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except ValueError:
        return None


async def import_tarifarios(
    file: UploadFile,
    repo: SqlAlchemyTarifarioRepository,
    prestador_repo: SqlAlchemyPrestadorRepository,
) -> dict[str, int]:
    rows = _read_csv(await file.read())
    created = 0
    for row in rows:
        pst_clave = (row.get("PST_CLAVE") or "").strip().upper()
        tipo = (row.get("TIPO_SERVICIO") or "").strip()
        vigencia_desde = _parse_date(row.get("VIGENCIA_DESDE") or "")
        if not pst_clave or not tipo or not vigencia_desde:
            continue
        prestador = await prestador_repo.get_by_nombre_corto(pst_clave)
        if not prestador:
            logger.warning(
                "import_tarifarios: PST_CLAVE '%s' no encontrada, fila omitida", pst_clave
            )
            continue
        try:
            costo_serv = float(row.get("COSTO_SERVICIO") or 0)
            costo_km = float(row.get("COSTO_KM") or 0)
        except ValueError:
            continue
        await repo.create(
            prestador_id=prestador.id,
            tipo_servicio=tipo,
            zona=(row.get("ZONA") or "").strip() or None,
            costo_servicio=costo_serv,
            costo_km=costo_km,
            vigencia_desde=vigencia_desde,
            vigencia_hasta=_parse_date(row.get("VIGENCIA_HASTA") or ""),
        )
        created += 1
    return {"creados": created}


# ─── Tabla KM ────────────────────────────────────────────────────────────────


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


async def import_tabla_km(
    file: UploadFile,
    repo: SqlAlchemyTablaKmRepository,
    prestador_repo: SqlAlchemyPrestadorRepository,
) -> dict[str, int]:
    rows = _read_csv(await file.read())
    created = 0
    for row in rows:
        pst_clave = (row.get("PST_CLAVE") or "").strip().upper()
        empresa = (row.get("EMPRESA") or "").strip()
        sucursal = (row.get("SUCURSAL") or "").strip()
        if not pst_clave or not empresa or not sucursal:
            continue
        prestador = await prestador_repo.get_by_nombre_corto(pst_clave)
        if not prestador:
            logger.warning("import_tabla_km: PST_CLAVE '%s' no encontrada, fila omitida", pst_clave)
            continue
        try:
            kms = float(row.get("KMS_RECORRIDO") or 0)
            kms_fact = float(row.get("KMS_A_FACTURAR") or 0)
            umbral = float(row.get("UMBRAL_VIATICO") or 30.0)
        except ValueError:
            continue
        aplica = (row.get("APLICA_VIATICO") or "").strip().upper() == "SI"
        await repo.create(
            prestador_id=prestador.id,
            spst_id=None,
            empresa_nombre=empresa,
            sucursal_nombre=sucursal,
            observaciones=(row.get("OBSERVACIONES") or "").strip() or None,
            domicilio_cliente=(row.get("DOMICILIO") or "").strip() or None,
            localidad_cliente=(row.get("LOCALIDAD") or "").strip() or None,
            provincia_cliente=(row.get("PROVINCIA") or "").strip() or None,
            kms_recorrido=kms,
            umbral_viatico=umbral,
            aplica_viatico=aplica,
            kms_a_facturar=kms_fact,
            url_maps=(row.get("URL_MAPS") or "").strip() or None,
        )
        created += 1
    return {"creados": created}
