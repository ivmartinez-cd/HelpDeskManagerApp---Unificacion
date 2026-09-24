"""Implementación Postgres del puerto ConsultaDespachosRepository: lo que lee la pantalla de
Despachados (tabla, bandeja "Requieren acción", tarjetas y contadores del menú). El SQL
vive en `_sql_consulta_despachos.py`."""

from collections.abc import Sequence
from dataclasses import fields
from datetime import date
from typing import Any

from sqlalchemy import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    ResultadoAccion,
    TipoAccion,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    FilaDespacho,
    FiltrosDespachos,
    Pagina,
    ResumenDespachos,
    UltimaAccion,
)
from src.modules.insumos.infrastructure.repositories._sql_consulta_despachos import (
    contar_filas,
    listar_filas,
    operativas_presentes,
    resumen_por_color,
)

_CAMPOS_CALCULADOS = {"color", "ultima_accion", "dias_habiles_para_limite"}
_CAMPOS_DIRECTOS = tuple(f.name for f in fields(FilaDespacho) if f.name not in _CAMPOS_CALCULADOS)
"""Campos de `FilaDespacho` que la consulta ya devuelve con su nombre y tipo final."""


class SqlAlchemyConsultaDespachosRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar(self, filtros: FiltrosDespachos, pagina: Pagina) -> list[FilaDespacho]:
        filas = (await self._session.execute(listar_filas(filtros, pagina))).mappings().all()
        return [_fila(fila) for fila in filas]

    async def contar(self, filtros: FiltrosDespachos) -> int:
        total: int = (await self._session.execute(contar_filas(filtros))).scalar_one()
        return total

    async def resumir(self, alcance_desde: date) -> ResumenDespachos:
        por_color = (await self._session.execute(resumen_por_color(alcance_desde))).mappings()
        operativas = (await self._session.execute(operativas_presentes(alcance_desde))).scalars()
        return _resumen(por_color.all(), tuple(operativas.all()))


def _fila(fila: RowMapping) -> FilaDespacho:
    return FilaDespacho(
        **{campo: fila[campo] for campo in _CAMPOS_DIRECTOS},
        color=ColorSemaforo(fila["color"]),
        ultima_accion=_ultima_accion(fila),
    )


def _ultima_accion(fila: RowMapping) -> UltimaAccion | None:
    if fila["accion_tipo"] is None:
        return None
    return UltimaAccion(
        tipo=TipoAccion(fila["accion_tipo"]),
        resultado=ResultadoAccion(fila["accion_resultado"]),
        usuario_nombre=fila["accion_usuario_nombre"],
        creada_en=fila["accion_creada_en"],
    )


def _resumen(filas: Sequence[RowMapping], operativas: tuple[str, ...]) -> ResumenDespachos:
    por_color: dict[ColorSemaforo, dict[str, Any]] = {
        ColorSemaforo(fila["color"]): dict(fila) for fila in filas
    }
    rojo = por_color.get(ColorSemaforo.ROJO, {})
    naranja = por_color.get(ColorSemaforo.NARANJA, {})
    return ResumenDespachos(
        por_color={c: por_color.get(c, {}).get("cantidad", 0) for c in ColorSemaforo},
        alertas_rojas=rojo.get("alertas_abiertas", 0),
        alertas_naranjas=naranja.get("alertas_abiertas", 0),
        naranjas_sin_accion=naranja.get("sin_accion", 0),
        limite_mas_proximo=rojo.get("limite_min"),
        operativas=operativas,
    )
