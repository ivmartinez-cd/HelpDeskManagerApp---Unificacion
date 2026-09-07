"""Búsquedas de incidentes relacionados que alimentan ALT003/ALT004/ALT010
(extraídas de `motor.py` por tamaño, §4). Comparan contra `incidentes_prestador`
(todo el histórico del PST), no solo la liquidación en curso."""

from collections.abc import Sequence

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.tarifario import TIPO_CORRECTIVO, TIPO_PREVENTIVO


def _similares_alt003(
    incidente: Incidente, incidentes_prestador: Sequence[Incidente]
) -> list[Incidente]:
    return [
        i
        for i in incidentes_prestador
        if i.id != incidente.id
        and _mismo_texto(i.empresa_nombre, incidente.empresa_nombre)
        and _mismo_texto(i.sucursal_nombre, incidente.sucursal_nombre)
        and i.fecha_cierre == incidente.fecha_cierre
        and (i.cant_km_cobrado or 0) > 0
    ]


def _mismo_texto(a: str | None, b: str | None) -> bool:
    return (a or "").strip().lower() == (b or "").strip().lower()


def _duplicados_alt004(
    incidente: Incidente, incidentes_prestador: Sequence[Incidente]
) -> list[Incidente]:
    return [
        i
        for i in incidentes_prestador
        if i.id != incidente.id and i.numero_incidente == incidente.numero_incidente
    ]


def _coincidencias_alt010(
    incidente: Incidente, incidentes_prestador: Sequence[Incidente]
) -> list[Incidente]:
    if not incidente.nro_serie or incidente.fecha_cierre is None:
        return []
    if incidente.tipo not in (TIPO_PREVENTIVO, TIPO_CORRECTIVO):
        return []
    tipo_opuesto = TIPO_CORRECTIVO if incidente.tipo == TIPO_PREVENTIVO else TIPO_PREVENTIVO
    periodo = (incidente.fecha_cierre.year, incidente.fecha_cierre.month)
    return [
        i
        for i in incidentes_prestador
        if i.id != incidente.id
        and i.nro_serie == incidente.nro_serie
        and i.tipo == tipo_opuesto
        and i.fecha_cierre is not None
        and (i.fecha_cierre.year, i.fecha_cierre.month) == periodo
    ]
