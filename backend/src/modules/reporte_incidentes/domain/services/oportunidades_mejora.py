"""Panel "Oportunidades de Mejora" (port de `insights.ts`).

Dos niveles: el titular (visitas cerradas sin reparar el equipo, un hecho
operativo) y el resto de las subcategorías con causa fuera del equipo,
rankeadas, marcando cuando una sucursal concentra los casos."""

from collections import Counter
from dataclasses import dataclass

from src.modules.reporte_incidentes.domain.entities.incidente import Incidente
from src.modules.reporte_incidentes.domain.services.reglas_taxonomia import (
    SUBCATEGORIAS_FUERA_DEL_EQUIPO,
    SUBCATEGORIAS_SIN_REPARACION,
)
from src.modules.reporte_incidentes.domain.services.resumen import SIN_DATO, porcentaje

UMBRAL_CONCENTRACION = 0.3
TOP_OPORTUNIDADES = 4


@dataclass(frozen=True, slots=True)
class ItemSinReparacion:
    subcategoria: str
    cantidad: int
    pct: int  # sobre el total de incidentes del período


@dataclass(frozen=True, slots=True)
class ItemMejora:
    categoria: str
    subcategoria: str
    cantidad: int
    pct: int
    sucursal_principal: str
    sucursal_principal_cantidad: int
    sucursal_principal_pct: int  # sobre los casos de esta subcategoría
    concentrado: bool


@dataclass(frozen=True, slots=True)
class OportunidadesMejora:
    total: int
    fuera_del_equipo_total: int
    fuera_del_equipo_pct: int
    sin_reparacion_total: int
    sin_reparacion_pct: int
    sin_reparacion_items: list[ItemSinReparacion]
    items: list[ItemMejora]


def _item_mejora(subcategoria: str, casos: list[Incidente], total: int) -> ItemMejora:
    por_sucursal = Counter(i.sucursal or SIN_DATO for i in casos)
    sucursal, cantidad = sorted(por_sucursal.items(), key=lambda kv: -kv[1])[0]
    return ItemMejora(
        categoria=casos[0].categoria or "",
        subcategoria=subcategoria,
        cantidad=len(casos),
        pct=porcentaje(len(casos), total),
        sucursal_principal=sucursal,
        sucursal_principal_cantidad=cantidad,
        sucursal_principal_pct=porcentaje(cantidad, len(casos)),
        concentrado=cantidad / len(casos) >= UMBRAL_CONCENTRACION,
    )


def _resto(fuera: list[Incidente], total: int) -> list[ItemMejora]:
    por_sub: dict[str, list[Incidente]] = {}
    for incidente in fuera:
        if incidente.subcategoria not in SUBCATEGORIAS_SIN_REPARACION:
            por_sub.setdefault(incidente.subcategoria or "", []).append(incidente)
    items = [_item_mejora(sub, casos, total) for sub, casos in por_sub.items()]
    return sorted(items, key=lambda i: -i.cantidad)[:TOP_OPORTUNIDADES]


def _sin_reparacion(casos: list[Incidente], total: int) -> list[ItemSinReparacion]:
    conteo = Counter(i.subcategoria or "" for i in casos)
    items = [ItemSinReparacion(s, c, porcentaje(c, total)) for s, c in conteo.items()]
    return sorted(items, key=lambda i: -i.cantidad)


def oportunidades_de_mejora(incidentes: list[Incidente]) -> OportunidadesMejora:
    total = len(incidentes)
    fuera = [i for i in incidentes if i.subcategoria in SUBCATEGORIAS_FUERA_DEL_EQUIPO]
    sin_reparacion = [i for i in fuera if i.subcategoria in SUBCATEGORIAS_SIN_REPARACION]
    return OportunidadesMejora(
        total=total,
        fuera_del_equipo_total=len(fuera),
        fuera_del_equipo_pct=porcentaje(len(fuera), total),
        sin_reparacion_total=len(sin_reparacion),
        sin_reparacion_pct=porcentaje(len(sin_reparacion), total),
        sin_reparacion_items=_sin_reparacion(sin_reparacion, total),
        items=_resto(fuera, total),
    )
