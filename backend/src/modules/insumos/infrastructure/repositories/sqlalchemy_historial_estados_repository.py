"""Implementación Postgres del puerto HistorialEstadosRepository
(`insumos_despacho_estado_historial`)."""

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.despachados.cambio_estado import CambioEstado
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca
from src.modules.insumos.infrastructure.models.despacho_estado_historial_model import (
    DespachoEstadoHistorialModel,
)


class SqlAlchemyHistorialEstadosRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def registrar(self, guia: str, estado: EstadoOca, color: ColorSemaforo) -> None:
        stmt = insert(DespachoEstadoHistorialModel).values(
            guia=guia,
            id_estado=estado.id_estado,
            estado=estado.estado,
            motivo=estado.motivo or "",
            sucursal=estado.sucursal_actual or "",
            fecha_estado=estado.fecha_estado,
            color=color.value,
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def listar_por_guia(self, guia: str) -> list[CambioEstado]:
        modelo = DespachoEstadoHistorialModel
        stmt = (
            select(modelo)
            .where(modelo.guia == guia)
            .order_by(modelo.observado_en.desc(), modelo.id.desc())
        )
        filas = (await self._session.execute(stmt)).scalars().all()
        return [_cambio(fila) for fila in filas]


def _cambio(fila: DespachoEstadoHistorialModel) -> CambioEstado:
    return CambioEstado(
        id_estado=fila.id_estado,
        estado=fila.estado,
        motivo=fila.motivo,
        sucursal=fila.sucursal,
        fecha_estado=fila.fecha_estado,
        color=ColorSemaforo(fila.color),
        observado_en=fila.observado_en,
    )
