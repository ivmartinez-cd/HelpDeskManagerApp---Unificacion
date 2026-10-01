"""Imports CSV de Prestadores/SPSTs y helpers comunes (los de Tarifarios/Tabla KM,
que a diferencia de estos hacen upsert, viven en `tarifarios.py`/`tabla_km.py`; los
exports en `presentation/_liq_csv_export.py`). Movido de presentation a application
por ADR-044: es lógica de negocio (parseo, duplicados, matching de prestador).

Convención de columnas:
  prestadores   → CLAVE, NOMBRE, CUIT, REGION
  spsts         → PST_CLAVE, NOMBRE, DOMICILIO, LOCALIDAD, PROVINCIA, ZONA
  tarifarios    → PST_CLAVE, TIPO_SERVICIO, SPST, COSTO_SERVICIO, COSTO_KM,
                  VIGENCIA_DESDE, VIGENCIA_HASTA (SPST = nombre, vacío =
                  tarifa genérica; ver `tarifarios.py`)
  tabla_km      → PST_CLAVE, EMPRESA, SUCURSAL, DOMICILIO, LOCALIDAD,
                  PROVINCIA, KMS_RECORRIDO, KMS_A_FACTURAR, UMBRAL_VIATICO,
                  APLICA_VIATICO, URL_MAPS, OBSERVACIONES
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import date

from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)
from src.modules.liquidaciones.domain.repositories.spst_repository import SpstRepository
from src.shared.infrastructure.celdas import desescapar_celda

logger = logging.getLogger(__name__)


def _read_csv(file_bytes: bytes) -> list[dict[str, str]]:
    text = file_bytes.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def _celda(row: dict[str, str], columna: str) -> str:
    return desescapar_celda((row.get(columna) or "").strip())


def _parse_date(val: str) -> date | None:
    val = val.strip()
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except ValueError:
        return None


async def _resolver_prestador(
    row: dict[str, str], prestador_repo: PrestadorRepository, contexto: str
) -> Prestador | None:
    pst_clave = _celda(row, "PST_CLAVE").upper()
    if not pst_clave:
        return None
    prestador = await prestador_repo.get_by_nombre_corto(pst_clave)
    if not prestador:
        logger.warning("%s: PST_CLAVE '%s' no encontrada, fila omitida", contexto, pst_clave)
    return prestador


# ─── Prestadores ─────────────────────────────────────────────────────────────


async def import_prestadores(
    contenido: bytes, repo: PrestadorRepository
) -> dict[str, int]:
    rows = _read_csv(contenido)
    created = 0
    for row in rows:
        clave = _celda(row, "CLAVE").upper()
        nombre = _celda(row, "NOMBRE")
        if not clave or not nombre or await repo.get_by_nombre_corto(clave):
            continue
        await repo.create(
            nombre=nombre,
            nombre_corto=clave,
            cuit=_celda(row, "CUIT") or None,
            region=_celda(row, "REGION") or None,
        )
        created += 1
    return {"creados": created}


# ─── SPSTs ───────────────────────────────────────────────────────────────────


async def import_spsts(
    contenido: bytes,
    repo: SpstRepository,
    prestador_repo: PrestadorRepository,
) -> dict[str, int]:
    rows = _read_csv(contenido)
    created = 0
    for row in rows:
        if await _importar_spst(row, repo, prestador_repo):
            created += 1
    return {"creados": created}


async def _importar_spst(
    row: dict[str, str],
    repo: SpstRepository,
    prestador_repo: PrestadorRepository,
) -> bool:
    nombre = _celda(row, "NOMBRE")
    if not nombre:
        return False
    prestador = await _resolver_prestador(row, prestador_repo, "import_spsts")
    if not prestador:
        return False
    await repo.create(
        prestador_id=prestador.id,
        nombre=nombre,
        domicilio=_celda(row, "DOMICILIO") or None,
        localidad=_celda(row, "LOCALIDAD") or None,
        provincia=_celda(row, "PROVINCIA") or None,
        zona_cobertura=_celda(row, "ZONA") or None,
    )
    return True


