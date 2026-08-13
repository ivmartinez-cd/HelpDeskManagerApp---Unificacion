import uuid
from typing import Protocol

from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride


class AsignacionOverrideRepository(Protocol):
    """Puerto de persistencia de overrides temporales de asignación (ver ADR-013)."""

    async def create(self, override: AsignacionOverride) -> None: ...

    async def list_all(self) -> list[AsignacionOverride]: ...

    async def get_by_id(self, override_id: uuid.UUID) -> AsignacionOverride | None: ...

    async def list_activos_por_ausente(
        self, operador_ausente_id: str
    ) -> list[AsignacionOverride]:
        """Overrides con estado ACTIVA para ese operador ausente, sin filtrar
        por fecha — catálogo chico por operador, el filtro de vigencia lo
        hace `resolver_operador_efectivo`."""
        ...

    async def cancelar(self, override_id: uuid.UUID) -> None: ...
