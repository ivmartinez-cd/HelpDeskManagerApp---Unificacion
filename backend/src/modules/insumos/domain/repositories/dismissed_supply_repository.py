"""Puerto de descarte de "pedido despachado sin confirmar entrega" (dismissed_supplies)."""

from typing import Protocol

from src.modules.insumos.domain.entities.dismissed_supply import DismissedSupply


class DismissedSupplyRepository(Protocol):
    async def mark_dismissed(
        self, supply_id: int, device_serial: str, hp_request_id: int | None = None
    ) -> None:
        """INSERT OR IGNORE: descartar dos veces el mismo pedido no rompe nada."""
        ...

    async def get_dismissed_ids(self, supply_ids: list[int]) -> set[int]:
        """Batch — usado por list_requests, que ya tiene el set exacto de candidatos."""
        ...

    async def get_all_dismissed_ids(self) -> set[int]:
        """Todo el set de descartes activos — usado por el dashboard, que matchea supplies
        al vuelo por request sin lista de candidatos previa."""
        ...

    async def get_pending_unignore(self) -> list[DismissedSupply]:
        """Descartes con IGNORE activo en HP SDS (hp_request_id no nulo) — candidatos a
        UNIGNORE una vez que el supply llegue a un estado final."""
        ...

    async def clear(self, supply_id: int) -> None:
        """Saca el descarte — deja de filtrarse en list_requests/dashboard."""
        ...
