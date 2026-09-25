from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.reporte_incidentes.domain.entities.categoria import Categoria
from src.modules.reporte_incidentes.infrastructure.models.taxonomia_models import (
    ReporteIncidentesCategoriaModel as CategoriaModel,
)
from src.modules.reporte_incidentes.infrastructure.models.taxonomia_models import (
    ReporteIncidentesSubcategoriaModel as SubcategoriaModel,
)


def _a_entidad(model: CategoriaModel) -> Categoria:
    return Categoria(
        nombre=model.nombre,
        color=model.color,
        descripcion=model.descripcion,
        subcategorias=tuple(s.nombre for s in model.subcategorias),
    )


def _subcategorias(categoria: Categoria) -> list[SubcategoriaModel]:
    return [SubcategoriaModel(nombre=n, orden=i) for i, n in enumerate(categoria.subcategorias)]


class SqlAlchemyTaxonomiaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar(self) -> list[Categoria]:
        stmt = select(CategoriaModel).order_by(CategoriaModel.orden, CategoriaModel.id)
        result = await self._session.execute(stmt)
        return [_a_entidad(m) for m in result.scalars().all()]

    async def crear(self, categoria: Categoria) -> None:
        ultimo = await self._session.scalar(select(func.max(CategoriaModel.orden)))
        self._session.add(
            CategoriaModel(
                nombre=categoria.nombre, color=categoria.color, descripcion=categoria.descripcion,
                orden=(ultimo + 1) if ultimo is not None else 0,
                subcategorias=_subcategorias(categoria),
            )
        )
        await self._session.flush()

    async def reemplazar(self, nombre_anterior: str, categoria: Categoria) -> None:
        model = await self._buscar(nombre_anterior)
        model.nombre = categoria.nombre
        model.color = categoria.color
        model.descripcion = categoria.descripcion
        # Borrar antes de insertar: el UNIQUE (categoria_id, nombre) chocaría si
        # una subcategoría se conserva con el mismo nombre.
        model.subcategorias.clear()
        await self._session.flush()
        model.subcategorias.extend(_subcategorias(categoria))
        await self._session.flush()

    async def eliminar(self, nombre: str) -> None:
        await self._session.execute(
            delete(CategoriaModel).where(func.lower(CategoriaModel.nombre) == nombre.lower())
        )

    async def _buscar(self, nombre: str) -> CategoriaModel:
        stmt = select(CategoriaModel).where(func.lower(CategoriaModel.nombre) == nombre.lower())
        return (await self._session.execute(stmt)).scalar_one()
