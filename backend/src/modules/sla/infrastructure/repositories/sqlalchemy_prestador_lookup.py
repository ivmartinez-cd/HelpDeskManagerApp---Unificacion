import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.prestadores.infrastructure.models.prestador_models import PrestadorModel


class SqlAlchemyPrestadorLookup:
    """Adaptador cruzado hacia prestadores — legal porque el contrato de
    import-linter `sla-domain-app-independent-from-prestadores` solo prohíbe
    la dependencia desde domain/application (mismo patrón que
    `modules.turnos` usa para leer `app_user` desde auth)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_siges_ids_por_operador(self, operador_id: uuid.UUID) -> list[int]:
        stmt = select(PrestadorModel.siges_empresa_id).where(
            PrestadorModel.operador_id == operador_id
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return list(rows)
