from typing import Protocol

from src.modules.sla.domain.entities.sla_snapshot import SlaSnapshot


class SlaSnapshotRepository(Protocol):
    """Puerto de persistencia del snapshot cacheado — un registro por período,
    reescrito en cada refresh (ver RefreshSlaSnapshot). Nunca pega contra
    Siges/MERCURIO, eso es responsabilidad exclusiva de SlaQueryGateway."""

    async def get(self, periodo: int) -> SlaSnapshot | None: ...

    async def upsert(self, snapshot: SlaSnapshot) -> None: ...
