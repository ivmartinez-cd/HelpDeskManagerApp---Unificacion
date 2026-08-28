"""Helpers puros del job que revierte descartes temporales (dismiss_request con
supply_id, no ignore_request) cuando el pedido asociado llega a un estado final en
Canal Directo — ver domain/entities/dismissed_supply.py y cd_state.INACTIVE_STATES."""

from src.modules.insumos.domain.entities.dismissed_supply import DismissedSupply
from src.modules.insumos.domain.value_objects.cd_state import INACTIVE_STATES


def find_supplies_ready_to_unignore(
    pending: list[DismissedSupply], statuses: dict[int, str]
) -> list[DismissedSupply]:
    return [d for d in pending if statuses.get(d.supply_id) in INACTIVE_STATES]


def build_unignore_comment(supply_id: int, estado: str) -> str:
    return (
        f"Pedido {supply_id} {estado} en Canal Directo — reactivado automáticamente "
        "desde HelpDesk Manager"
    )
