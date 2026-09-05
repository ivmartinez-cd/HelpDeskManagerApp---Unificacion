from dataclasses import replace

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.infrastructure.models.estim_receso_model import EstimRecesoModel


class SqlAlchemyRecesosRepository:
    """Sin commit: el límite transaccional vive en `get_db` (scope="function",
    ADR-030)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar(self, id_grupo_economico: int) -> list[RecesoDto]:
        stmt = select(EstimRecesoModel).where(
            EstimRecesoModel.id_grupo_economico == id_grupo_economico
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_dto(row) for row in rows]

    async def crear(self, receso_sin_id: RecesoDto) -> RecesoDto:
        row = EstimRecesoModel(
            id_grupo_economico=receso_sin_id.id_grupo_economico,
            id_anexo=receso_sin_id.id_anexo,
            fecha_desde=receso_sin_id.fecha_desde,
            fecha_hasta=receso_sin_id.fecha_hasta,
            descripcion=receso_sin_id.descripcion,
        )
        self._session.add(row)
        await self._session.flush()
        return replace(receso_sin_id, id=row.id)

    async def eliminar(self, id_receso: int) -> None:
        await self._session.execute(
            delete(EstimRecesoModel).where(EstimRecesoModel.id == id_receso)
        )


def _to_dto(row: EstimRecesoModel) -> RecesoDto:
    return RecesoDto(
        id=row.id,
        id_grupo_economico=row.id_grupo_economico,
        id_anexo=row.id_anexo,
        fecha_desde=row.fecha_desde,
        fecha_hasta=row.fecha_hasta,
        descripcion=row.descripcion,
    )
