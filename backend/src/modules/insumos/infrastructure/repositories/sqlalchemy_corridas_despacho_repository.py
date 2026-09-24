"""Implementación Postgres del puerto CorridasDespachoRepository (`insumos_despacho_corrida`).

`terminada_en` se marca con `clock_timestamp()` y no con `now()`: `now()` es la hora de
inicio de la transacción, así que una corrida iniciada y terminada en la misma transacción
quedaría con duración cero.
"""

from typing import Any, cast

from sqlalchemy import CursorResult, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.despachados.corrida import (
    Corrida,
    OrigenCorrida,
    ResumenCorrida,
)
from src.modules.insumos.infrastructure.models.despacho_corrida_model import (
    DespachoCorridaModel,
)


class SqlAlchemyCorridasDespachoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def iniciar(self, origen: OrigenCorrida, usuario_nombre: str | None) -> Corrida:
        stmt = (
            insert(DespachoCorridaModel)
            .values(origen=origen.value, usuario_nombre=usuario_nombre)
            .returning(DespachoCorridaModel.id, DespachoCorridaModel.iniciada_en)
        )
        fila = (await self._session.execute(stmt)).one()
        await self._session.flush()
        return Corrida(
            id=fila.id, origen=origen, iniciada_en=fila.iniciada_en, usuario_nombre=usuario_nombre
        )

    async def terminar(self, corrida_id: int, resumen: ResumenCorrida) -> None:
        stmt = (
            update(DespachoCorridaModel)
            .where(DespachoCorridaModel.id == corrida_id)
            .values(
                terminada_en=func.clock_timestamp(),
                envios_nuevos=resumen.envios_nuevos,
                consultas_ok=resumen.consultas_ok,
                consultas_error=resumen.consultas_error,
                error=resumen.error,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def cerrar_interrumpidas(self, motivo: str) -> int:
        stmt = (
            update(DespachoCorridaModel)
            .where(DespachoCorridaModel.terminada_en.is_(None))
            .values(terminada_en=func.clock_timestamp(), error=motivo)
        )
        resultado = cast(CursorResult[Any], await self._session.execute(stmt))
        await self._session.flush()
        return int(resultado.rowcount)

    async def ultima(self) -> Corrida | None:
        stmt = select(DespachoCorridaModel).order_by(
            DespachoCorridaModel.iniciada_en.desc(), DespachoCorridaModel.id.desc()
        )
        fila = (await self._session.execute(stmt.limit(1))).scalar_one_or_none()
        return None if fila is None else _corrida(fila)

    async def ultima_terminada(self) -> Corrida | None:
        stmt = (
            select(DespachoCorridaModel)
            .where(DespachoCorridaModel.terminada_en.is_not(None))
            .order_by(DespachoCorridaModel.terminada_en.desc(), DespachoCorridaModel.id.desc())
        )
        fila = (await self._session.execute(stmt.limit(1))).scalar_one_or_none()
        return None if fila is None else _corrida(fila)


def _corrida(fila: DespachoCorridaModel) -> Corrida:
    return Corrida(
        id=fila.id,
        origen=OrigenCorrida(fila.origen),
        iniciada_en=fila.iniciada_en,
        usuario_nombre=fila.usuario_nombre,
        terminada_en=fila.terminada_en,
        resumen=ResumenCorrida(
            envios_nuevos=fila.envios_nuevos,
            consultas_ok=fila.consultas_ok,
            consultas_error=fila.consultas_error,
            error=fila.error,
        ),
    )
