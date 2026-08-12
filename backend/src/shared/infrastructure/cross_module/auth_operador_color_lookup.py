"""Adaptador cruzado: implementa el puerto `OperadorColorLookup` que define
auth, resolviendo contra el catálogo de operadores de contadores.

Vive acá (no en `src.modules.auth` ni en `src.modules.contadores`) porque el
contrato de import-linter `auth-independent-from-contadores` prohíbe que
CUALQUIER capa de auth importe contadores. `shared` no tiene esa restricción
con ningún módulo de negocio — es el único lugar del repo donde el "puerto en
auth, adaptador con la dependencia real, wiring en la capa de composición" se
puede cablear sin violar contratos. auth sigue sin saber que Gestión o
contadores existen; solo conoce su propio Protocol."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.infrastructure.repositories.sqlalchemy_calendario_repository import (
    SqlAlchemyCalendarEventRepository,
)


class SqlAlchemyOperadorColorLookup:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = SqlAlchemyCalendarEventRepository(session)

    async def find_color_by_nombre(self, nombre: str) -> str | None:
        operador = await self._repo.find_operador_by_nombre(nombre)
        return operador.color if operador else None
