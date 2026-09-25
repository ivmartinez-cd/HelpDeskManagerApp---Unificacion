"""Lo que muestra el dashboard a partir del reporte armado (port de
`dashboard/page.tsx` + `IncidentsTable.tsx`).

KPIs, evolución y tabla usan la selección filtrada; los gráficos, las
oportunidades de mejora y el panel de pendientes usan el período completo
(son los que sirven para navegar)."""

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from src.modules.reporte_incidentes.application.use_cases.armar_reporte import ReporteArmado
from src.modules.reporte_incidentes.domain.entities.incidente import Incidente
from src.modules.reporte_incidentes.domain.services.filtros import (
    Filtros,
    OpcionesFiltro,
    aplicar_filtros,
    opciones_filtro,
    sanear_filtros,
)
from src.modules.reporte_incidentes.domain.services.oportunidades_mejora import (
    OportunidadesMejora,
    oportunidades_de_mejora,
)
from src.modules.reporte_incidentes.domain.services.resumen import Resumen, resumir
from src.modules.reporte_incidentes.domain.services.tipificacion import (
    COLOR_PENDIENTE,
    COLOR_SIN_CLASIFICAR,
    PENDIENTE,
    SIN_CLASIFICAR,
)

CampoOrden = Literal[
    "numero", "fecha", "sucursal", "descripcion",
    "causa", "solucion", "categoria", "subcategoria",
]
_CAMPOS_BUSQUEDA = (
    "numero", "descripcion", "causa", "solucion",
    "sucursal", "tecnico", "categoria", "subcategoria",
)


@dataclass(frozen=True, slots=True)
class VistaReporte:
    reporte: ReporteArmado
    filtros: Filtros
    opciones: OpcionesFiltro
    seleccion: Resumen
    completo: Resumen
    oportunidades: OportunidadesMejora
    colores: dict[str, str]
    pendientes_revision: int


def colores_categorias(reporte: ReporteArmado) -> dict[str, str]:
    colores = {c.nombre: c.color for c in reporte.taxonomia}
    return {**colores, SIN_CLASIFICAR: COLOR_SIN_CLASIFICAR, PENDIENTE: COLOR_PENDIENTE}


def componer_vista(reporte: ReporteArmado, crudos: Filtros) -> VistaReporte:
    opciones = opciones_filtro(reporte.incidentes)
    filtros = sanear_filtros(crudos, opciones)
    nombres = [c.nombre for c in reporte.taxonomia]
    seleccion = aplicar_filtros(reporte.incidentes, filtros)
    return VistaReporte(
        reporte=reporte,
        filtros=filtros,
        opciones=opciones,
        seleccion=resumir(seleccion, nombres),
        completo=resumir(reporte.incidentes, nombres),
        oportunidades=oportunidades_de_mejora(reporte.incidentes),
        colores=colores_categorias(reporte),
        pendientes_revision=len(pendientes_de_revision(reporte)),
    )


def pendientes_de_revision(reporte: ReporteArmado) -> list[Incidente]:
    return [i for i in reporte.incidentes if i.categoria == PENDIENTE]


def buscar(incidentes: list[Incidente], texto: str) -> list[Incidente]:
    """Contiene, sin distinguir mayúsculas, en cualquiera de los campos visibles."""
    q = texto.strip().lower()
    if not q:
        return incidentes
    return [
        i for i in incidentes
        if any(q in (getattr(i, c) or "").lower() for c in _CAMPOS_BUSQUEDA)
    ]


def _natural(valor: str) -> tuple[tuple[int, int | str], ...]:
    """Aproxima `localeCompare("es", {numeric: true})`: números por valor, texto sin acentos."""
    base = unicodedata.normalize("NFD", valor).encode("ascii", "ignore").decode().casefold()
    return tuple((0, int(p)) if p.isdigit() else (1, p) for p in re.split(r"(\d+)", base) if p)


def ordenar(incidentes: list[Incidente], campo: CampoOrden | None, desc: bool) -> list[Incidente]:
    """Sin campo, el orden del reporte. Vacíos al final en ambos sentidos."""
    if campo is None:
        return incidentes
    con = [i for i in incidentes if getattr(i, campo)]
    sin = [i for i in incidentes if not getattr(i, campo)]
    return sorted(con, key=lambda i: _natural(getattr(i, campo)), reverse=desc) + sin
