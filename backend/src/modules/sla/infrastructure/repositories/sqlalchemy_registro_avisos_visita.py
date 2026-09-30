from sqlalchemy import select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.sla.domain.repositories.avisos_visita_sucursal import ParAvisado
from src.modules.sla.infrastructure.models.aviso_visita_sucursal_model import (
    AvisoVisitaSucursalModel as M,
)


class SqlAlchemyRegistroAvisosVisita:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ya_avisados(self, pares: list[ParAvisado]) -> set[ParAvisado]:
        if not pares:
            return set()
        clave = tuple_(M.id_incidente_mda, M.id_incidente_visita)
        stmt = select(M.id_incidente_mda, M.id_incidente_visita).where(clave.in_(pares))
        rows = await self._session.execute(stmt)
        return {(r.id_incidente_mda, r.id_incidente_visita) for r in rows}

    async def registrar(self, pares: list[ParAvisado]) -> None:
        valores = [{"id_incidente_mda": m, "id_incidente_visita": v} for m, v in pares]
        await self._session.execute(insert(M).values(valores).on_conflict_do_nothing())
