"""Mapeo de las filas pyodbc de la consulta agrupada a la entidad de dominio.

Acceso por nombre de columna (pyodbc.Row lo expone como atributo), no por
índice posicional: si la consulta cambia de orden, esto falla ruidoso con
AttributeError en vez de mapear silenciosamente un campo en otro. La consulta
ya agrupa por (técnico, categoría) en SQL — `pivot_conteos` solo pasa de "una
fila por técnico+categoría" a "una fila por técnico" con las 5 categorías
como columnas, igual que el resumen `Lista!I1:J9` del Excel.

El filtro `LEFT(Den_Comercial,2)='CD'` de la consulta (ver `query.py`) deja
pasar además de técnicos algunas filas de `Empresa` que no son personas
(mesa de ayuda, prestadores, DaaS) y que en Siges también empiezan con "CD" —
`_TECNICOS_EXCLUIDOS` las saca del resumen, a pedido explícito del usuario
2026-08-25."""

import unicodedata
from dataclasses import dataclass
from typing import Any

from src.modules.bono_tecnicos.domain.entities.conteo_tecnico import ConteoTecnico

_TECNICOS_EXCLUIDOS = frozenset(
    {
        "PRESTADOR SERVICIO TECNICO",
        "PRESTADOR DE SERVICIO TECNICO",
        "MESA DE AYUDA",
        "HECTOR ARGUELLO",
        "DIEGO ESTEVEZ",
        "DAAS",
    }
)


def _normalizar(tecnico: str) -> str:
    sin_acentos = unicodedata.normalize("NFKD", tecnico).encode("ascii", "ignore").decode()
    sin_prefijo = sin_acentos.removeprefix("CD - ")
    return sin_prefijo.strip().upper()


@dataclass(frozen=True, slots=True)
class _FilaCategoria:
    tecnico: str
    id_tecnico: int
    categoria: str
    cantidad: int


def map_row(row: Any) -> _FilaCategoria:
    return _FilaCategoria(
        tecnico=str(row.Tecnico).strip() if row.Tecnico is not None else "",
        id_tecnico=int(row.IdTecnico),
        categoria=str(row.Categoria).strip() if row.Categoria is not None else "",
        cantidad=int(row.Cantidad),
    )


def _agrupar_por_tecnico(filas: list[_FilaCategoria]) -> dict[tuple[str, int], dict[str, int]]:
    por_tecnico: dict[tuple[str, int], dict[str, int]] = {}
    for fila in filas:
        if _normalizar(fila.tecnico) in _TECNICOS_EXCLUIDOS:
            continue
        clave = (fila.tecnico, fila.id_tecnico)
        por_tecnico.setdefault(clave, {})[fila.categoria] = fila.cantidad
    return por_tecnico


def pivot_conteos(filas: list[_FilaCategoria], periodo: int) -> list[ConteoTecnico]:
    por_tecnico = _agrupar_por_tecnico(filas)
    return [
        ConteoTecnico(
            tecnico=tecnico,
            id_tecnico=id_tecnico,
            periodo=periodo,
            correctivo=categorias.get("Correctivo", 0),
            preventivo=categorias.get("Preventivo", 0),
            inst_des=categorias.get("InstDes", 0),
            pre_correctivo=categorias.get("PreCorrectivo", 0),
            entrega_insumos=categorias.get("EntregaInsumos", 0),
        )
        for (tecnico, id_tecnico), categorias in por_tecnico.items()
    ]
