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

`modificaciones` lleva el detalle campo a campo de cada `cambio` (antes/después,
ver `campos_modificados_incidente.py`) — lo consume
`application/use_cases/_registrar_modificaciones.py` para avisarle a la TL que el
prestador tocó algo, sin que el motor de reglas se entere de esto (ver ADR-038).
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import UUID

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.services.campos_modificados_incidente import (
    campos_modificados,
)
from src.modules.liquidaciones.domain.value_objects.incidente_actualizado import (
    IncidenteActualizado,
)
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    IncidenteImportado,
)
from src.modules.liquidaciones.domain.value_objects.incidente_modificado import (
    IncidenteModificado,
)


@dataclass(frozen=True)
class DiffIncidentes:
    altas: list[IncidenteImportado]
    cambios: list[IncidenteActualizado]
    bajas: list[UUID]
    ambiguos: int
    modificaciones: list[IncidenteModificado] = field(default_factory=list)


def reconciliar_incidentes(
    locales: Sequence[Incidente], remotos: Sequence[IncidenteImportado]
) -> DiffIncidentes:
    locales_por_clave = _agrupar_locales(locales)
    remotos_por_clave = _agrupar_remotos(remotos)

    ambiguos = sum(1 for filas in locales_por_clave.values() if len(filas) > 1)
    ambiguos += sum(1 for filas in remotos_por_clave.values() if len(filas) > 1)

    altas = _detectar_altas(locales_por_clave, remotos_por_clave)
    cambios, modificaciones = _detectar_cambios(locales_por_clave, remotos_por_clave)
    bajas = _detectar_bajas(locales_por_clave, remotos_por_clave)

    return DiffIncidentes(
        altas=altas, cambios=cambios, bajas=bajas, ambiguos=ambiguos, modificaciones=modificaciones
    )


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
) -> tuple[list[IncidenteActualizado], list[IncidenteModificado]]:
    cambios = []
    modificaciones = []
    for clave, remotas in remotos_por_clave.items():
        if len(remotas) != 1:
            continue
        locales = locales_por_clave.get(clave)
        if locales is None or len(locales) != 1:
            continue
        local, remoto = locales[0], remotas[0]
        campos = campos_modificados(local, remoto)
        if campos:
            cambios.append(_a_actualizado(local.id, remoto))
            modificaciones.append(
                IncidenteModificado(local.id, local.numero_incidente, tuple(campos))
            )
    return cambios, modificaciones


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
