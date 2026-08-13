import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.prestadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.prestadores.domain.services.operador_efectivo import resolver_operador_efectivo
from src.modules.prestadores.infrastructure.models.prestador_models import PrestadorModel
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_asignacion_override_repository import (  # noqa: E501
    SqlAlchemyAsignacionOverrideRepository,
)


class SqlAlchemyPrestadorLookup:
    """Adaptador cruzado hacia prestadores — legal porque el contrato de
    import-linter `sla-domain-app-independent-from-prestadores` solo prohíbe
    la dependencia desde domain/application (mismo patrón que
    `modules.turnos` usa para leer `app_user` desde auth).

    "Mis PST" incluye tanto los propios (asignación permanente, salvo que un
    override vigente hoy los haya cubierto con otro operador) como los que
    estoy cubriendo yo por un override activo (ver ADR-013) — así el
    reemplazante también ve los incidentes SLA vencidos del ausente."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._overrides = SqlAlchemyAsignacionOverrideRepository(session)

    async def get_siges_ids_por_operador(self, operador_id: uuid.UUID) -> list[int]:
        propios = await self._propios_no_cubiertos(operador_id)
        cubiertos = await self._cubiertos_por(operador_id)
        return sorted(set(propios) | set(cubiertos))

    async def _propios_no_cubiertos(self, operador_id: uuid.UUID) -> list[int]:
        hoy = date.today()
        reglas = await self._overrides.list_activos_por_ausente(operador_id)
        prestadores = await self._prestadores_de(operador_id)
        return [
            p.siges_empresa_id
            for p in prestadores
            if resolver_operador_efectivo(operador_id, p.id, hoy, reglas) == operador_id
        ]

    async def _cubiertos_por(self, operador_id: uuid.UUID) -> list[int]:
        hoy = date.today()
        cubro_a = await self._overrides.list_activos_por_reemplazante(operador_id)
        resultado: list[int] = []
        for ausente_id in {o.operador_ausente_id for o in cubro_a}:
            reglas = [o for o in cubro_a if o.operador_ausente_id == ausente_id]
            resultado += await self._siges_ids_resueltos(ausente_id, reglas, operador_id, hoy)
        return resultado

    async def _siges_ids_resueltos(
        self,
        ausente_id: uuid.UUID,
        reglas: list[AsignacionOverride],
        operador_id: uuid.UUID,
        hoy: date,
    ) -> list[int]:
        prestadores = await self._prestadores_de(ausente_id)
        return [
            p.siges_empresa_id
            for p in prestadores
            if resolver_operador_efectivo(ausente_id, p.id, hoy, reglas) == operador_id
        ]

    async def _prestadores_de(self, operador_id: uuid.UUID) -> list[PrestadorModel]:
        stmt = select(PrestadorModel).where(PrestadorModel.operador_id == operador_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return list(rows)
