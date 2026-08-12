"""Resolución compartida por varios evaluadores: tabla_km/zona/tarifario aplicable a un
incidente, y el criterio de "mismo corredor" (ALT002 y ALT005 lo usan idéntico — en el
legacy vivía duplicado en dos archivos con un comentario "must match", acá es una sola
función)."""

import uuid
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario

if TYPE_CHECKING:
    from datetime import date

UMBRAL_CORREDOR_KM = 50.0


def clave_empresa_sucursal(empresa: str | None, sucursal: str | None) -> tuple[str, str]:
    return ((empresa or "").strip().lower(), (sucursal or "").strip().lower())


def indexar_tablas_km(tablas_km: Sequence[TablaKm]) -> dict[tuple[str, str], TablaKm]:
    return {clave_empresa_sucursal(t.empresa_nombre, t.sucursal_nombre): t for t in tablas_km}


def resolver_tabla_km(
    incidente: Incidente, indice: Mapping[tuple[str, str], TablaKm]
) -> TablaKm | None:
    return indice.get(clave_empresa_sucursal(incidente.empresa_nombre, incidente.sucursal_nombre))


def resolver_zona(tabla_km: TablaKm | None, spsts_por_id: Mapping[uuid.UUID, Spst]) -> str | None:
    if tabla_km is None or tabla_km.spst_id is None:
        return None
    spst = spsts_por_id.get(tabla_km.spst_id)
    return spst.zona if spst else None


def resolver_tarifario(
    incidente: Incidente, zona: str | None, tarifarios: Sequence[Tarifario]
) -> Tarifario | None:
    if incidente.fecha_cierre is None:
        return None
    candidatos = [
        t for t in tarifarios if _tarifario_aplica(t, incidente.tipo, incidente.fecha_cierre, zona)
    ]
    if not candidatos:
        return None
    return max(candidatos, key=lambda t: _orden_tarifario(t, zona))


def _tarifario_aplica(t: Tarifario, tipo_servicio: str, fecha: "date", zona: str | None) -> bool:
    if t.tipo_servicio != tipo_servicio:
        return False
    if t.vigencia_desde > fecha:
        return False
    if t.vigencia_hasta is not None and t.vigencia_hasta < fecha:
        return False
    return t.zona == zona or t.zona is None


def _orden_tarifario(t: Tarifario, zona: str | None) -> tuple[int, "date"]:
    coincide_zona = 1 if (zona is not None and t.zona == zona) else 0
    return (coincide_zona, t.vigencia_desde)


def mismo_corredor(t1: TablaKm, t2: TablaKm) -> bool:
    if _misma_localidad(t1, t2):
        return True
    return _mismo_spst_dentro_del_umbral(t1, t2)


def _misma_localidad(t1: TablaKm, t2: TablaKm) -> bool:
    l1, l2 = t1.localidad_cliente, t2.localidad_cliente
    if not l1 or not l1.strip() or not l2:
        return False
    return l1.strip().lower() == l2.strip().lower()


def _mismo_spst_dentro_del_umbral(t1: TablaKm, t2: TablaKm) -> bool:
    if not t1.spst_id or t2.spst_id != t1.spst_id:
        return False
    if t1.kms_recorrido is None or t2.kms_recorrido is None:
        return False
    return abs(t1.kms_recorrido - t2.kms_recorrido) <= UMBRAL_CORREDOR_KM
