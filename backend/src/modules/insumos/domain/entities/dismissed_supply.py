"""Pedido despachado sin confirmar entrega, descartado a mano (tabla dismissed_supplies).

Clave por supply_id, no por hp_request_id: HP SDS puede reemitir la solicitud con otro
ID mientras el mismo pedido siga pendiente. `hp_request_id` no-None es la solicitud que
se marcó IGNORE en HP SDS — permite mandarle UNIGNORE cuando el supply llegue a un
estado final (ver application/jobs/dismiss_reconciliation.py); None es un descarte
permanente que no se revierte solo (ver application/use_cases/ignore_request.py).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DismissedSupply:
    supply_id: int
    device_serial: str
    hp_request_id: int | None = None
