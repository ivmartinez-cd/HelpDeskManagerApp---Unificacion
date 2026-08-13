"""Imports CSV de la configuración de liquidaciones (los exports viven en
`_liq_csv_export.py` — separados para respetar el límite §4 de 300 líneas).

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

from src.modules.liquidaciones.application.use_cases.config_tarifarios import CreateTarifario
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.tabla_km import UMBRAL_VIATICO_DEFAULT
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_spst_repository import (
    SqlAlchemySpstRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (
    SqlAlchemyTablaKmRepository,
)

logger = logging.getLogger(__name__)


def _read_csv(file_bytes: bytes) -> list[dict[str, str]]:
    text = file_bytes.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def _celda(row: dict[str, str], columna: str) -> str:
    return (row.get(columna) or "").strip()


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
    file: UploadFile, repo: SqlAlchemyPrestadorRepository
) -> dict[str, int]:
    rows = _read_csv(await file.read())
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
    file: UploadFile,
    repo: SqlAlchemySpstRepository,
    prestador_repo: SqlAlchemyPrestadorRepository,
) -> dict[str, int]:
    rows = _read_csv(await file.read())
    created = 0
    for row in rows:
        if await _importar_spst(row, repo, prestador_repo):
            created += 1
    return {"creados": created}


async def _importar_spst(
    row: dict[str, str],
    repo: SqlAlchemySpstRepository,
    prestador_repo: SqlAlchemyPrestadorRepository,
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
        zona=_celda(row, "ZONA") or None,
    )
    return True


# ─── Tarifarios ──────────────────────────────────────────────────────────────


async def import_tarifarios(
    file: UploadFile,
    crear_tarifario: CreateTarifario,
    prestador_repo: PrestadorRepository,
) -> dict[str, int]:
    """Cada alta va por el use case `CreateTarifario` (no repo directo) para que el
    grupo afectado quede recadenado, igual que el alta manual desde la UI."""
    rows = _read_csv(await file.read())
    created = 0
    for row in rows:
        if await _importar_tarifario(row, crear_tarifario, prestador_repo):
            created += 1
    return {"creados": created}


async def _importar_tarifario(
    row: dict[str, str],
    crear_tarifario: CreateTarifario,
    prestador_repo: PrestadorRepository,
) -> bool:
    tipo = _celda(row, "TIPO_SERVICIO")
    vigencia_desde = _parse_date(_celda(row, "VIGENCIA_DESDE"))
    if not tipo or not vigencia_desde:
        return False
    prestador = await _resolver_prestador(row, prestador_repo, "import_tarifarios")
    costos = _leer_costos(row) if prestador else None
    if prestador is None or costos is None:
        return False
    await _alta_tarifario(crear_tarifario, row, prestador, tipo, vigencia_desde, costos)
    return True


async def _alta_tarifario(
    crear_tarifario: CreateTarifario,
    row: dict[str, str],
    prestador: Prestador,
    tipo: str,
    vigencia_desde: date,
    costos: tuple[float, float],
) -> None:
    await crear_tarifario.execute(
        prestador_id=prestador.id,
        tipo_servicio=tipo,
        zona=_celda(row, "ZONA") or None,
        costo_servicio=costos[0],
        costo_km=costos[1],
        vigencia_desde=vigencia_desde,
        vigencia_hasta=_parse_date(_celda(row, "VIGENCIA_HASTA")),
    )


def _leer_costos(row: dict[str, str]) -> tuple[float, float] | None:
    try:
        return float(row.get("COSTO_SERVICIO") or 0), float(row.get("COSTO_KM") or 0)
    except ValueError:
        logger.warning(
            "import_tarifarios: fila de '%s' omitida por costo ilegible "
            "(COSTO_SERVICIO=%r, COSTO_KM=%r)",
            _celda(row, "PST_CLAVE").upper(),
            row.get("COSTO_SERVICIO"),
            row.get("COSTO_KM"),
        )
        return None


# ─── Tabla KM ────────────────────────────────────────────────────────────────


async def import_tabla_km(
    file: UploadFile,
    repo: SqlAlchemyTablaKmRepository,
    prestador_repo: SqlAlchemyPrestadorRepository,
) -> dict[str, int]:
    rows = _read_csv(await file.read())
    created = 0
    for row in rows:
        if await _importar_fila_tabla_km(row, repo, prestador_repo):
            created += 1
    return {"creados": created}


async def _importar_fila_tabla_km(
    row: dict[str, str],
    repo: SqlAlchemyTablaKmRepository,
    prestador_repo: SqlAlchemyPrestadorRepository,
) -> bool:
    empresa = _celda(row, "EMPRESA")
    sucursal = _celda(row, "SUCURSAL")
    if not empresa or not sucursal:
        return False
    prestador = await _resolver_prestador(row, prestador_repo, "import_tabla_km")
    if not prestador:
        return False
    kms = _leer_kms(row, empresa, sucursal)
    if kms is None:
        return False
    await _crear_tabla_km(row, repo, prestador, empresa, sucursal, kms)
    return True


def _leer_kms(
    row: dict[str, str], empresa: str, sucursal: str
) -> tuple[float, float, float] | None:
    try:
        return (
            float(row.get("KMS_RECORRIDO") or 0),
            float(row.get("KMS_A_FACTURAR") or 0),
            float(row.get("UMBRAL_VIATICO") or UMBRAL_VIATICO_DEFAULT),
        )
    except ValueError:
        logger.warning(
            "import_tabla_km: fila de '%s' (%s / %s) omitida por kms ilegibles "
            "(KMS_RECORRIDO=%r, KMS_A_FACTURAR=%r, UMBRAL_VIATICO=%r)",
            _celda(row, "PST_CLAVE").upper(),
            empresa,
            sucursal,
            row.get("KMS_RECORRIDO"),
            row.get("KMS_A_FACTURAR"),
            row.get("UMBRAL_VIATICO"),
        )
        return None


async def _crear_tabla_km(
    row: dict[str, str],
    repo: SqlAlchemyTablaKmRepository,
    prestador: Prestador,
    empresa: str,
    sucursal: str,
    kms: tuple[float, float, float],
) -> None:
    await repo.create(
        prestador_id=prestador.id,
        spst_id=None,
        empresa_nombre=empresa,
        sucursal_nombre=sucursal,
        observaciones=_celda(row, "OBSERVACIONES") or None,
        domicilio_cliente=_celda(row, "DOMICILIO") or None,
        localidad_cliente=_celda(row, "LOCALIDAD") or None,
        provincia_cliente=_celda(row, "PROVINCIA") or None,
        kms_recorrido=kms[0],
        umbral_viatico=kms[2],
        aplica_viatico=_celda(row, "APLICA_VIATICO").upper() == "SI",
        kms_a_facturar=kms[1],
        url_maps=_celda(row, "URL_MAPS") or None,
    )
