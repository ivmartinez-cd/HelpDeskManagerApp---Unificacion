"""KPIs y series de los gráficos (port de `aggregate.ts:summarize`).

Los empates se resuelven como en el legacy: sort estable sobre el orden de
aparición (categorías: primero el orden de la taxonomía, después "Sin
Clasificar" y por último lo que aparezca, p. ej. "Pendiente de revision")."""

from collections import Counter
from dataclasses import dataclass

from src.modules.reporte_incidentes.domain.entities.incidente import Incidente
from src.modules.reporte_incidentes.domain.services.tipificacion import (
    SIN_CLASIFICAR,
    SIN_SUBCATEGORIA,
)

SIN_DATO = "—"
_TOP_SUCURSALES = 6
_TOP_SUBCATEGORIAS = 10


@dataclass(frozen=True, slots=True)
class Conteo:
    nombre: str
    cantidad: int


@dataclass(frozen=True, slots=True)
class ConteoSubcategoria:
    nombre: str
    cantidad: int
    categoria: str


@dataclass(frozen=True, slots=True)
class Resumen:
    total: int
    categoria_principal: str
    categoria_principal_cantidad: int
    categoria_principal_pct: int
    sucursal_principal: str
    sucursal_principal_cantidad: int
    categorias: list[Conteo]
    subcategorias: list[ConteoSubcategoria]
    evolucion: list[Conteo]  # nombre = fecha ISO del día
    sucursales: list[Conteo]


def porcentaje(parte: int, total: int) -> int:
    """Redondeo de `Math.round` (mitades hacia arriba), no el bancario de Python."""
    return int(parte * 100 / total + 0.5) if total > 0 else 0


def _ranking(conteo: Counter[str]) -> list[Conteo]:
    return sorted((Conteo(n, c) for n, c in conteo.items()), key=lambda c: -c.cantidad)


def contar_categorias(incidentes: list[Incidente], taxonomia: list[str]) -> list[Conteo]:
    conteo: Counter[str] = Counter(dict.fromkeys([*taxonomia, SIN_CLASIFICAR], 0))
    conteo.update(i.categoria or SIN_CLASIFICAR for i in incidentes)
    return [c for c in _ranking(conteo) if c.cantidad > 0]


def contar_subcategorias(incidentes: list[Incidente]) -> list[ConteoSubcategoria]:
    conteo: Counter[str] = Counter()
    categoria_de: dict[str, str] = {}
    for incidente in incidentes:
        nombre = (incidente.subcategoria or "").strip() or SIN_SUBCATEGORIA
        conteo[nombre] += 1
        categoria_de.setdefault(nombre, incidente.categoria or SIN_CLASIFICAR)
    ranking = _ranking(conteo)[:_TOP_SUBCATEGORIAS]
    return [ConteoSubcategoria(c.nombre, c.cantidad, categoria_de[c.nombre]) for c in ranking]


def contar_sucursales(incidentes: list[Incidente]) -> list[Conteo]:
    conteo = Counter(i.sucursal or SIN_DATO for i in incidentes)
    return _ranking(conteo)[:_TOP_SUCURSALES]


def evolucion_diaria(incidentes: list[Incidente]) -> list[Conteo]:
    conteo = Counter(i.fecha for i in incidentes)
    return sorted((Conteo(d, c) for d, c in conteo.items()), key=lambda c: c.nombre)


def resumir(incidentes: list[Incidente], taxonomia: list[str]) -> Resumen:
    """`taxonomia` = nombres de categorías en el orden configurado."""
    total = len(incidentes)
    categorias = contar_categorias(incidentes, taxonomia)
    sucursales = contar_sucursales(incidentes)
    top_cat = categorias[0] if categorias else Conteo(SIN_DATO, 0)
    top_suc = sucursales[0] if sucursales else Conteo(SIN_DATO, 0)
    return Resumen(
        total=total,
        categoria_principal=top_cat.nombre,
        categoria_principal_cantidad=top_cat.cantidad,
        categoria_principal_pct=porcentaje(top_cat.cantidad, total),
        sucursal_principal=top_suc.nombre,
        sucursal_principal_cantidad=top_suc.cantidad,
        categorias=categorias,
        subcategorias=contar_subcategorias(incidentes),
        evolucion=evolucion_diaria(incidentes),
        sucursales=sucursales,
    )
