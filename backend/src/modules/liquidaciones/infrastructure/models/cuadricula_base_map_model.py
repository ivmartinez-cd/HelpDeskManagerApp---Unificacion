import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, delete, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column

from src.modules.liquidaciones.domain.entities.cuadricula_base_map import CuadriculaBaseMap
from src.shared.infrastructure.database.base import Base


class CuadriculaBaseMapModel(Base):
    __tablename__ = "cuadricula_base_maps"
    __table_args__ = (
        UniqueConstraint(
            "prestador_id",
            "cuadricula",
            name="uq_cuadricula_base_maps_prestador_cuadricula",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    prestador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prestadores.id", ondelete="CASCADE"), nullable=False
    )
    cuadricula: Mapped[str] = mapped_column(String, nullable=False)
    siges_base_sucursal_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    def to_entity(self) -> CuadriculaBaseMap:
        return CuadriculaBaseMap(
            id=self.id,
            prestador_id=self.prestador_id,
            cuadricula=self.cuadricula,
            siges_base_sucursal_id=self.siges_base_sucursal_id,
            created_at=self.created_at,
        )


class SqlAlchemyCuadriculaBaseMapRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_prestador(self, prestador_id: uuid.UUID) -> list[CuadriculaBaseMap]:
        result = await self._session.execute(
            select(CuadriculaBaseMapModel)
            .where(CuadriculaBaseMapModel.prestador_id == prestador_id)
            .order_by(CuadriculaBaseMapModel.cuadricula)
        )
        return [m.to_entity() for m in result.scalars()]

    async def upsert(
        self,
        *,
        prestador_id: uuid.UUID,
        cuadricula: str,
        siges_base_sucursal_id: int,
    ) -> CuadriculaBaseMap:
        result = await self._session.execute(
            select(CuadriculaBaseMapModel).where(
                CuadriculaBaseMapModel.prestador_id == prestador_id,
                CuadriculaBaseMapModel.cuadricula == cuadricula,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            model = CuadriculaBaseMapModel(
                prestador_id=prestador_id,
                cuadricula=cuadricula,
                siges_base_sucursal_id=siges_base_sucursal_id,
            )
            self._session.add(model)
        else:
            model.siges_base_sucursal_id = siges_base_sucursal_id
        await self._session.flush()
        return model.to_entity()

    async def delete(self, *, prestador_id: uuid.UUID, cuadricula: str) -> None:
        await self._session.execute(
            delete(CuadriculaBaseMapModel).where(
                CuadriculaBaseMapModel.prestador_id == prestador_id,
                CuadriculaBaseMapModel.cuadricula == cuadricula,
            )
        )

