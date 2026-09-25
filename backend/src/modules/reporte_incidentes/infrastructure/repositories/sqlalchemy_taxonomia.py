from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.reporte_incidentes.domain.entities.categoria import Categoria
from src.modules.reporte_incidentes.infrastructure.models.taxonomia_models import (
    ReporteIncidentesCategoriaModel,
)


def _a_entidad(model: ReporteIncidentesCategoriaModel) -> Categoria:
    return Categoria(
        nombre=model.nombre,
        color=model.color,
        descripcion=model.descripcion,
        subcategorias=tuple(s.nombre for s in model.subcategorias),
    )


class SqlAlchemyTaxonomiaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar(self) -> list[Categoria]:
        stmt = select(ReporteIncidentesCategoriaModel).order_by(
            ReporteIncidentesCategoriaModel.orden, ReporteIncidentesCategoriaModel.id
        )
        result = await self._session.execute(stmt)
        return [_a_entidad(m) for m in result.scalars().all()]
