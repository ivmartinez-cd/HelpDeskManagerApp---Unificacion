"""Implementación Postgres del puerto AccionesDespachoRepository (`insumos_despacho_accion`).
Solo se agregan filas: no hay edición ni borrado."""

from dataclasses import asdict

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    AccionNueva,
    AccionRegistrada,
    ResultadoAccion,
    TipoAccion,
)
from src.modules.insumos.infrastructure.models.despacho_accion_model import DespachoAccionModel


class SqlAlchemyAccionesDespachoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def agregar(self, accion: AccionNueva) -> AccionRegistrada:
        stmt = (
            insert(DespachoAccionModel)
            .values(
                guia=accion.guia,
                tipo=accion.tipo.value,
                detalle=accion.detalle,
                resultado=accion.resultado.value,
                cerro_alerta=accion.cerro_alerta,
                usuario_id=accion.usuario_id,
                usuario_nombre=accion.usuario_nombre,
            )
            .returning(DespachoAccionModel.id, DespachoAccionModel.creada_en)
        )
        fila = (await self._session.execute(stmt)).one()
        await self._session.flush()
        return AccionRegistrada(id=fila.id, creada_en=fila.creada_en, **asdict(accion))

    async def listar_por_guia(self, guia: str) -> list[AccionRegistrada]:
        stmt = (
            select(DespachoAccionModel)
            .where(DespachoAccionModel.guia == guia)
            .order_by(DespachoAccionModel.creada_en.desc(), DespachoAccionModel.id.desc())
        )
        filas = (await self._session.execute(stmt)).scalars().all()
        return [_accion(fila) for fila in filas]


def _accion(fila: DespachoAccionModel) -> AccionRegistrada:
    return AccionRegistrada(
        id=fila.id,
        guia=fila.guia,
        tipo=TipoAccion(fila.tipo),
        detalle=fila.detalle,
        resultado=ResultadoAccion(fila.resultado),
        cerro_alerta=fila.cerro_alerta,
        usuario_id=fila.usuario_id,
        usuario_nombre=fila.usuario_nombre,
        creada_en=fila.creada_en,
    )
