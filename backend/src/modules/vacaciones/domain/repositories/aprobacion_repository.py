import uuid
from typing import Protocol

from src.modules.vacaciones.domain.entities.aprobacion import Aprobacion


class AprobacionRepository(Protocol):
    async def add(self, aprobacion: Aprobacion) -> None: ...

    async def list_por_solicitud(self, solicitud_id: uuid.UUID) -> list[Aprobacion]: ...

    async def list_por_solicitudes(
        self, solicitud_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[Aprobacion]]: ...
