"""Filtros transversales del reporte (port de `filters.ts`).

Se aplican sobre el set ya tipificado para re-escopar KPIs, evolución y tabla;
los gráficos y las oportunidades de mejora usan siempre el período completo.
Valor vacío = sin filtro."""

import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Literal

from src.modules.reporte_incidentes.domain.entities.incidente import Incidente
from src.modules.reporte_incidentes.domain.services.tipificacion import (
    SIN_CLASIFICAR,
    SIN_SUBCATEGORIA,
)

Dimension = Literal["sucursal", "categoria", "subcategoria"]


@dataclass(frozen=True, slots=True)
class Filtros:
    sucursal: str = ""
    categoria: str = ""
    subcategoria: str = ""

    @property
    def activos(self) -> bool:
        return bool(self.sucursal or self.categoria or self.subcategoria)


@dataclass(frozen=True, slots=True)
class OpcionFiltro:
    valor: str
    cantidad: int


@dataclass(frozen=True, slots=True)
class OpcionesFiltro:
    sucursales: list[OpcionFiltro]
    categorias: list[OpcionFiltro]
    subcategorias: list[OpcionFiltro]


def valor_dimension(incidente: Incidente, dimension: Dimension) -> str:
    if dimension == "sucursal":
        return (incidente.sucursal or "").strip()
    if dimension == "categoria":
        return (incidente.categoria or SIN_CLASIFICAR).strip()
    return (incidente.subcategoria or "").strip() or SIN_SUBCATEGORIA


def _clave_orden(valor: str) -> str:
    # Aproxima `localeCompare(..., "es")`: sin distinguir mayúsculas ni acentos.
    sin_acentos = unicodedata.normalize("NFD", valor).encode("ascii", "ignore").decode()
    return sin_acentos.casefold()


def _contar(incidentes: list[Incidente], dimension: Dimension) -> list[OpcionFiltro]:
    conteo = Counter(v for i in incidentes if (v := valor_dimension(i, dimension)))
    opciones = [OpcionFiltro(v, c) for v, c in conteo.items()]
    return sorted(opciones, key=lambda o: (-o.cantidad, _clave_orden(o.valor)))


def opciones_filtro(incidentes: list[Incidente]) -> OpcionesFiltro:
    """Siempre sobre el período completo: sirven para sanear y para mostrar conteos."""
    return OpcionesFiltro(
        sucursales=_contar(incidentes, "sucursal"),
        categorias=_contar(incidentes, "categoria"),
        subcategorias=_contar(incidentes, "subcategoria"),
    )


def _conservar(valor: str, opciones: list[OpcionFiltro]) -> str:
    return valor if valor and any(o.valor == valor for o in opciones) else ""


def sanear_filtros(crudos: Filtros, opciones: OpcionesFiltro) -> Filtros:
    """Descarta valores que no existen en el período (p. ej. tras cambiar de mes)."""
    return Filtros(
        sucursal=_conservar(crudos.sucursal, opciones.sucursales),
        categoria=_conservar(crudos.categoria, opciones.categorias),
        subcategoria=_conservar(crudos.subcategoria, opciones.subcategorias),
    )


def _coincide(incidente: Incidente, filtros: Filtros) -> bool:
    pares: tuple[tuple[Dimension, str], ...] = (
        ("sucursal", filtros.sucursal),
        ("categoria", filtros.categoria),
        ("subcategoria", filtros.subcategoria),
    )
    return all(not v or valor_dimension(incidente, d) == v for d, v in pares)


def aplicar_filtros(incidentes: list[Incidente], filtros: Filtros) -> list[Incidente]:
    return [i for i in incidentes if _coincide(i, filtros)]
