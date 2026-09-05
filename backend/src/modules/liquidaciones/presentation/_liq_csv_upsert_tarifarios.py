"""Import CSV de Tarifarios — a diferencia de Prestadores/SPSTs (`_liq_csv.py`),
hace upsert: reimportar el mismo CSV (el flujo obvio para corregir un error:
exportar, editar, volver a cargar) antes duplicaba cada fila en vez de
actualizarla. El de Tabla KM vive en `_liq_csv_upsert_tabla_km.py` — separados
para respetar el límite §4 de 300 líneas (y las funciones cortas, de 20).

La columna `ZONA` del CSV legacy pasó a `SPST` (nombre del SPST del mismo
prestador, o vacío = tarifa genérica) — ver `Tarifario.spst_id`."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from fastapi import UploadFile

from src.modules.liquidaciones.application.use_cases.config_tarifarios import (
    CreateTarifario,
    UpdateTarifario,
)
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)
from src.modules.liquidaciones.domain.repositories.spst_repository import SpstRepository
from src.modules.liquidaciones.domain.repositories.tarifario_repository import (
    TarifarioRepository,
)
from src.modules.liquidaciones.presentation._liq_csv import (
    _celda,
    _parse_date,
    _read_csv,
    _resolver_prestador,
)

logger = logging.getLogger(__name__)

_Clave = tuple[str, UUID | None, date]
_SPST_DESCONOCIDO = object()  # sentinel: distinto de None (= genérica, válido)


@dataclass(frozen=True)
class _FilaTarifario:
    prestador_id: UUID
    tipo_servicio: str
    spst_id: UUID | None
    vigencia_desde: date
    vigencia_hasta: date | None
    costo_servicio: float
    costo_km: float


@dataclass
class _Contexto:
    """Repos de escritura + caches por prestador (índice de vigencias, nombres
    de SPST) — agrupados para no arrastrar 5+ parámetros por función."""

    crear_tarifario: CreateTarifario
    actualizar_tarifario: UpdateTarifario
    prestador_repo: PrestadorRepository
    tarifario_repo: TarifarioRepository
    spst_repo: SpstRepository
    indices: dict[UUID, dict[_Clave, Tarifario]] = field(default_factory=dict)
    spsts_por_nombre: dict[UUID, dict[str, UUID]] = field(default_factory=dict)


def _clave(f: _FilaTarifario) -> _Clave:
    return (f.tipo_servicio, f.spst_id, f.vigencia_desde)


async def import_tarifarios(
    file: UploadFile,
    crear_tarifario: CreateTarifario,
    actualizar_tarifario: UpdateTarifario,
    prestador_repo: PrestadorRepository,
    tarifario_repo: TarifarioRepository,
    spst_repo: SpstRepository,
) -> dict[str, int]:
    """Upsert por (prestador, tipo_servicio, spst_id, vigencia_desde) — esa es
    la clave real de una vigencia (`_recadenado.py`). Igual costo/vigencia_hasta
    ya cargado = sin cambios; distinto = actualiza esa vigencia in-place (no
    crea una nueva); ausente = alta normal (recadenada, como el manual)."""
    rows = _read_csv(await file.read())
    ctx = _Contexto(
        crear_tarifario, actualizar_tarifario, prestador_repo, tarifario_repo, spst_repo
    )
    contadores = {"creados": 0, "actualizados": 0, "sinCambios": 0, "descartadas": 0}
    for row in rows:
        contadores[await _importar_fila(row, ctx)] += 1
    return contadores


async def _importar_fila(row: dict[str, str], ctx: _Contexto) -> str:
    fila = await _leer_fila(row, ctx)
    if fila is None:
        return "descartadas"
    indice = await _indice(fila.prestador_id, ctx)
    existente = indice.get(_clave(fila))
    if existente is None:
        indice[_clave(fila)] = await _crear(ctx.crear_tarifario, fila)
        return "creados"
    if _sin_cambios(existente, fila):
        return "sinCambios"
    indice[_clave(fila)] = await _actualizar(ctx.actualizar_tarifario, existente.id, fila)
    return "actualizados"


async def _leer_fila(row: dict[str, str], ctx: _Contexto) -> _FilaTarifario | None:
    tipo = _celda(row, "TIPO_SERVICIO")
    vigencia_desde = _parse_date(_celda(row, "VIGENCIA_DESDE"))
    if not tipo or not vigencia_desde:
        return None
    if (base := await _resolver_prestador_y_costos(row, ctx)) is None:
        return None
    prestador, costos = base
    spst_id = await _resolver_spst(row, prestador, ctx)
    if spst_id is _SPST_DESCONOCIDO:
        return None
    return _FilaTarifario(
        prestador_id=prestador.id,
        tipo_servicio=tipo,
        spst_id=spst_id,
        vigencia_desde=vigencia_desde,
        vigencia_hasta=_parse_date(_celda(row, "VIGENCIA_HASTA")),
        costo_servicio=costos[0],
        costo_km=costos[1],
    )


async def _resolver_prestador_y_costos(
    row: dict[str, str], ctx: _Contexto
) -> tuple[Prestador, tuple[float, float]] | None:
    prestador = await _resolver_prestador(row, ctx.prestador_repo, "import_tarifarios")
    costos = _leer_costos(row) if prestador else None
    if prestador is None or costos is None:
        return None
    return prestador, costos


async def _resolver_spst(row: dict[str, str], prestador: Prestador, ctx: _Contexto) -> UUID | None:
    nombre = _celda(row, "SPST")
    if not nombre:
        return None  # genérica, sin SPST específico
    if prestador.id not in ctx.spsts_por_nombre:
        filas = await ctx.spst_repo.list_by_prestador(prestador.id)
        ctx.spsts_por_nombre[prestador.id] = {s.nombre.strip().lower(): s.id for s in filas}
    spst_id = ctx.spsts_por_nombre[prestador.id].get(nombre.strip().lower())
    if spst_id is None:
        logger.warning(
            "import_tarifarios: SPST '%s' no encontrado para '%s', fila omitida",
            nombre, prestador.nombre_corto,
        )
        return _SPST_DESCONOCIDO  # type: ignore[return-value]
    return spst_id


async def _indice(prestador_id: UUID, ctx: _Contexto) -> dict[_Clave, Tarifario]:
    if prestador_id not in ctx.indices:
        filas = await ctx.tarifario_repo.list_by_prestador(prestador_id)
        ctx.indices[prestador_id] = {
            (t.tipo_servicio, t.spst_id, t.vigencia_desde): t for t in filas
        }
    return ctx.indices[prestador_id]


def _sin_cambios(existente: Tarifario, f: _FilaTarifario) -> bool:
    return (existente.costo_servicio, existente.costo_km, existente.vigencia_hasta) == (
        f.costo_servicio, f.costo_km, f.vigencia_hasta,
    )


async def _crear(crear_tarifario: CreateTarifario, f: _FilaTarifario) -> Tarifario:
    return await crear_tarifario.execute(
        prestador_id=f.prestador_id, tipo_servicio=f.tipo_servicio, spst_id=f.spst_id,
        costo_servicio=f.costo_servicio, costo_km=f.costo_km,
        vigencia_desde=f.vigencia_desde, vigencia_hasta=f.vigencia_hasta,
    )


async def _actualizar(
    actualizar_tarifario: UpdateTarifario, tarifario_id: UUID, f: _FilaTarifario
) -> Tarifario:
    return await actualizar_tarifario.execute(
        tarifario_id, prestador_id=f.prestador_id, tipo_servicio=f.tipo_servicio,
        spst_id=f.spst_id, costo_servicio=f.costo_servicio, costo_km=f.costo_km,
        vigencia_desde=f.vigencia_desde, vigencia_hasta=f.vigencia_hasta,
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
