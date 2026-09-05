"""Import CSV de Tabla KM — a diferencia de Prestadores/SPSTs (`_liq_csv.py`),
hace upsert: reimportar el mismo CSV (el flujo obvio para corregir un error:
exportar, editar, volver a cargar) antes duplicaba cada fila en vez de
actualizarla. El de Tarifarios vive en `_liq_csv_upsert_tarifarios.py` —
separados para respetar el límite §4 de 300 líneas (y las funciones cortas,
de 20)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from fastapi import UploadFile

from src.modules.liquidaciones.application.use_cases.config_tabla_km import (
    CreateTablaKm,
    TablaKmDatos,
    UpdateTablaKm,
)
from src.modules.liquidaciones.domain.entities.tabla_km import UMBRAL_VIATICO_DEFAULT, TablaKm
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository
from src.modules.liquidaciones.domain.services.motor_reglas._resolucion import (
    clave_empresa_sucursal,
)
from src.modules.liquidaciones.presentation._liq_csv import (
    _celda,
    _read_csv,
    _resolver_prestador,
)

logger = logging.getLogger(__name__)

_Clave = tuple[str, str]


@dataclass(frozen=True)
class _FilaTablaKm:
    prestador_id: UUID
    empresa_nombre: str
    sucursal_nombre: str
    kms_recorrido: float
    kms_a_facturar: float
    umbral_viatico: float
    observaciones: str | None
    domicilio_cliente: str | None
    localidad_cliente: str | None
    provincia_cliente: str | None
    aplica_viatico: bool
    url_maps: str | None


def _clave(f: _FilaTablaKm) -> _Clave:
    return clave_empresa_sucursal(f.empresa_nombre, f.sucursal_nombre)


async def import_tabla_km(
    file: UploadFile,
    crear: CreateTablaKm,
    actualizar: UpdateTablaKm,
    prestador_repo: PrestadorRepository,
    tabla_km_repo: TablaKmRepository,
) -> tuple[dict[str, int], set[UUID]]:
    """Upsert por (prestador, empresa, sucursal), mismo criterio de matching que
    el motor de reglas. El 2do elemento: prestadores con filas NUEVAS — el
    caller corre "Vincular SPST" sobre cada uno (el CSV no trae SPST)."""
    rows = _read_csv(await file.read())
    contadores = {"creados": 0, "actualizados": 0, "sinCambios": 0, "descartadas": 0}
    indices: dict[UUID, dict[_Clave, TablaKm]] = {}
    tocados: set[UUID] = set()
    for row in rows:
        resultado, prestador_id = await _importar_fila(
            row, crear, actualizar, prestador_repo, tabla_km_repo, indices
        )
        _acumular(contadores, tocados, resultado, prestador_id)
    return contadores, tocados


def _acumular(
    contadores: dict[str, int], tocados: set[UUID], resultado: str, prestador_id: UUID | None
) -> None:
    contadores[resultado] += 1
    if resultado == "creados" and prestador_id is not None:
        tocados.add(prestador_id)


async def _importar_fila(
    row: dict[str, str],
    crear: CreateTablaKm,
    actualizar: UpdateTablaKm,
    prestador_repo: PrestadorRepository,
    tabla_km_repo: TablaKmRepository,
    indices: dict[UUID, dict[_Clave, TablaKm]],
) -> tuple[str, UUID | None]:
    fila = await _leer_fila(row, prestador_repo)
    if fila is None:
        return "descartadas", None
    indice = await _indice(fila.prestador_id, tabla_km_repo, indices)
    existente = indice.get(_clave(fila))
    if existente is None:
        indice[_clave(fila)] = await _crear(crear, fila)
        return "creados", fila.prestador_id
    if _sin_cambios(existente, fila):
        return "sinCambios", fila.prestador_id
    indice[_clave(fila)] = await _actualizar(actualizar, existente, fila)
    return "actualizados", fila.prestador_id


async def _leer_fila(
    row: dict[str, str], prestador_repo: PrestadorRepository
) -> _FilaTablaKm | None:
    empresa, sucursal = _celda(row, "EMPRESA"), _celda(row, "SUCURSAL")
    if not empresa or not sucursal:
        return None
    prestador = await _resolver_prestador(row, prestador_repo, "import_tabla_km")
    kms = _leer_kms(row, empresa, sucursal) if prestador else None
    if prestador is None or kms is None:
        return None
    return _armar_fila(row, prestador.id, empresa, sucursal, kms)


def _armar_fila(
    row: dict[str, str],
    prestador_id: UUID,
    empresa: str,
    sucursal: str,
    kms: tuple[float, float, float],
) -> _FilaTablaKm:
    return _FilaTablaKm(
        prestador_id=prestador_id, empresa_nombre=empresa, sucursal_nombre=sucursal,
        kms_recorrido=kms[0], kms_a_facturar=kms[1], umbral_viatico=kms[2],
        observaciones=_celda(row, "OBSERVACIONES") or None,
        domicilio_cliente=_celda(row, "DOMICILIO") or None,
        localidad_cliente=_celda(row, "LOCALIDAD") or None,
        provincia_cliente=_celda(row, "PROVINCIA") or None,
        aplica_viatico=_celda(row, "APLICA_VIATICO").upper() == "SI",
        url_maps=_celda(row, "URL_MAPS") or None,
    )


async def _indice(
    prestador_id: UUID, repo: TablaKmRepository, indices: dict[UUID, dict[_Clave, TablaKm]]
) -> dict[_Clave, TablaKm]:
    if prestador_id not in indices:
        filas = await repo.list_by_prestador(prestador_id)
        indices[prestador_id] = {
            clave_empresa_sucursal(f.empresa_nombre, f.sucursal_nombre): f for f in filas
        }
    return indices[prestador_id]


def _datos(f: _FilaTablaKm, *, spst_id: UUID | None) -> TablaKmDatos:
    return TablaKmDatos(
        prestador_id=f.prestador_id,
        # El CSV no trae SPST — preserva el que ya tenía la fila (el caller
        # pasa `existente.spst_id`) en vez de borrarlo en cada reimport.
        spst_id=spst_id,
        empresa_nombre=f.empresa_nombre,
        sucursal_nombre=f.sucursal_nombre,
        observaciones=f.observaciones,
        domicilio_cliente=f.domicilio_cliente,
        localidad_cliente=f.localidad_cliente,
        provincia_cliente=f.provincia_cliente,
        kms_recorrido=f.kms_recorrido,
        umbral_viatico=f.umbral_viatico,
        aplica_viatico=f.aplica_viatico,
        kms_a_facturar=f.kms_a_facturar,
        url_maps=f.url_maps,
    )


def _sin_cambios(existente: TablaKm, f: _FilaTablaKm) -> bool:
    datos = _datos(f, spst_id=existente.spst_id)
    return (
        existente.observaciones, existente.domicilio_cliente, existente.localidad_cliente,
        existente.provincia_cliente, existente.kms_recorrido, existente.umbral_viatico,
        existente.aplica_viatico, existente.kms_a_facturar, existente.url_maps,
    ) == (
        datos.observaciones, datos.domicilio_cliente, datos.localidad_cliente,
        datos.provincia_cliente, datos.kms_recorrido, datos.umbral_viatico,
        datos.aplica_viatico, datos.kms_a_facturar, datos.url_maps,
    )


async def _crear(crear: CreateTablaKm, f: _FilaTablaKm) -> TablaKm:
    return await crear.execute(_datos(f, spst_id=None))


async def _actualizar(actualizar: UpdateTablaKm, existente: TablaKm, f: _FilaTablaKm) -> TablaKm:
    return await actualizar.execute(existente.id, _datos(f, spst_id=existente.spst_id))


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
            "import_tabla_km: fila de '%s' (%s/%s) omitida por kms ilegibles "
            "(KMS_RECORRIDO=%r, KMS_A_FACTURAR=%r, UMBRAL_VIATICO=%r)",
            _celda(row, "PST_CLAVE").upper(), empresa, sucursal,
            row.get("KMS_RECORRIDO"), row.get("KMS_A_FACTURAR"), row.get("UMBRAL_VIATICO"),
        )
        return None
