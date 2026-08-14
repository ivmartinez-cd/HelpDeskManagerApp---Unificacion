from typing import Protocol

from src.modules.sla.domain.entities.pendientes_snapshot import PendientesSnapshot


class PendientesSnapshotRepository(Protocol):
    async def get(self) -> PendientesSnapshot | None: ...
    async def upsert(self, snapshot: PendientesSnapshot) -> None: ...
