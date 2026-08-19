"""Reconciliación de incidentes entre lo local y lo que reporta AyC — sync-time
diff, espejo de `conciliar_alertas.py`.

Acá el "trabajo previo" a preservar no es una decisión de la TL sino la identidad
(`incidente_id`) del incidente: `alertas.incidente_id` es `ON DELETE CASCADE`, y
`conciliar_alertas` indexa el triage de la TL por ese id. Por eso un incidente que
sigue existiendo remotamente NUNCA se borra y recrea — solo se actualiza in-place
(clasificado en `cambios`, con el mismo `incidente_id`). Solo se borra un incidente
si AyC dejó de reportarlo (`bajas`).

Clave de matching: la parte numérica de `numero_incidente`. El mismo incidente
puede llegar con o sin el dígito verificador módulo-10 según si la liquidación se
cargó por CSV (legacy: `"839551-5"`) o por el sync SOAP (id crudo: `"838937"`) —
verificado contra datos reales de producción (liquidaciones 3925-1/3928-8 vs
3907-5/3906-6/3905-7). Sin esta normalización, un desajuste de formato entre ambos
orígenes produciría 100% bajas + 100% altas — borrado y recreación masiva con
pérdida de triage. Un `numero_incidente` duplicado tras normalizar (local o
remoto) es ambiguo — no se toca, se cuenta en `ambiguos`.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.value_objects.incidente_actualizado import (
    IncidenteActualizado,
)
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    IncidenteImportado,
)

_TOLERANCIA_FLOAT = 0.005


@dataclass(frozen=True)
class DiffIncidentes:
    altas: list[IncidenteImportado]
    cambios: list[IncidenteActualizado]
    bajas: list[UUID]
    ambiguos: int


def reconciliar_incidentes(
    locales: Sequence[Incidente], remotos: Sequence[IncidenteImportado]
) -> DiffIncidentes:
    locales_por_clave = _agrupar_locales(locales)
    remotos_por_clave = _agrupar_remotos(remotos)

    ambiguos = sum(1 for filas in locales_por_clave.values() if len(filas) > 1)
    ambiguos += sum(1 for filas in remotos_por_clave.values() if len(filas) > 1)

    altas = _detectar_altas(locales_por_clave, remotos_por_clave)
    cambios = _detectar_cambios(locales_por_clave, remotos_por_clave)
    bajas = _detectar_bajas(locales_por_clave, remotos_por_clave)

    return DiffIncidentes(altas=altas, cambios=cambios, bajas=bajas, ambiguos=ambiguos)


def _clave(numero_incidente: str) -> str:
    return numero_incidente.split("-")[0].strip()


def _agrupar_locales(locales: Sequence[Incidente]) -> dict[str, list[Incidente]]:
    grupos: dict[str, list[Incidente]] = {}
    for item in locales:
        grupos.setdefault(_clave(item.numero_incidente), []).append(item)
    return grupos


def _agrupar_remotos(
    remotos: Sequence[IncidenteImportado],
) -> dict[str, list[IncidenteImportado]]:
    grupos: dict[str, list[IncidenteImportado]] = {}
    for item in remotos:
        grupos.setdefault(_clave(item.numero_incidente), []).append(item)
    return grupos


def _detectar_altas(
    locales_por_clave: dict[str, list[Incidente]],
    remotos_por_clave: dict[str, list[IncidenteImportado]],
) -> list[IncidenteImportado]:
    return [
        remotas[0]
        for clave, remotas in remotos_por_clave.items()
        if len(remotas) == 1 and clave not in locales_por_clave
    ]


def _detectar_bajas(
    locales_por_clave: dict[str, list[Incidente]],
    remotos_por_clave: dict[str, list[IncidenteImportado]],
) -> list[UUID]:
    return [
        locales[0].id
        for clave, locales in locales_por_clave.items()
        if len(locales) == 1 and clave not in remotos_por_clave
    ]


def _detectar_cambios(
    locales_por_clave: dict[str, list[Incidente]],
    remotos_por_clave: dict[str, list[IncidenteImportado]],
) -> list[IncidenteActualizado]:
    cambios = []
    for clave, remotas in remotos_por_clave.items():
        if len(remotas) != 1:
            continue
        locales = locales_por_clave.get(clave)
        if locales is None or len(locales) != 1:
            continue
        local, remoto = locales[0], remotas[0]
        if _difiere(local, remoto):
            cambios.append(_a_actualizado(local.id, remoto))
    return cambios


def _difiere(local: Incidente, remoto: IncidenteImportado) -> bool:
    return (
        _str_difiere(local.tipo, remoto.tipo)
        or _str_difiere(local.empresa_nombre, remoto.empresa_nombre)
        or _str_difiere(local.sucursal_nombre, remoto.sucursal_nombre)
        or _str_difiere(local.nro_serie, remoto.nro_serie)
        or _fecha_difiere(local.fecha_cierre, remoto.fecha_cierre)
        or local.pasa_it != remoto.pasa_it
        or _float_difiere(local.costo_servicio_cobrado, remoto.costo_servicio_cobrado)
        or _float_difiere(local.cant_km_cobrado, remoto.cant_km_cobrado)
        or _float_difiere(local.costo_km_cobrado, remoto.costo_km_cobrado)
        or _float_difiere(local.total_viaje_cobrado, remoto.total_viaje_cobrado)
        or _float_difiere(local.costo_total_cobrado, remoto.costo_total_cobrado)
    )


def _str_difiere(local: str | None, remoto: str) -> bool:
    return (local or "") != remoto


def _fecha_difiere(local: date | None, remoto: date | None) -> bool:
    return local != remoto


def _float_difiere(local: float, remoto: float) -> bool:
    return abs(local - remoto) > _TOLERANCIA_FLOAT


def _a_actualizado(incidente_id: UUID, remoto: IncidenteImportado) -> IncidenteActualizado:
    return IncidenteActualizado(
        incidente_id=incidente_id,
        rubro=remoto.rubro,
        tipo=remoto.tipo,
        empresa_nombre=remoto.empresa_nombre,
        sucursal_nombre=remoto.sucursal_nombre,
        nro_serie=remoto.nro_serie,
        fecha_cierre=remoto.fecha_cierre,
        costo_servicio_cobrado=remoto.costo_servicio_cobrado,
        cant_km_cobrado=remoto.cant_km_cobrado,
        costo_km_cobrado=remoto.costo_km_cobrado,
        total_viaje_cobrado=remoto.total_viaje_cobrado,
        costo_total_cobrado=remoto.costo_total_cobrado,
        pasa_it=remoto.pasa_it,
    )
