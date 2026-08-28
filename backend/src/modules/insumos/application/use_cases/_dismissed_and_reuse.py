"""Post-procesado de ListRequests tras la asociación pedido↔solicitud: ocultar filas con
un pedido despachado sin confirmar entrega ya descartado a mano, y avisar cuando el
consumable_serial de la fila ya generó otro pedido antes (informativo). Separado de
list_requests.py porque ese archivo ya está cerca del tamaño máximo (§4)."""

from src.modules.insumos.application.dtos.request_rows import RequestRow
from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.repositories.dismissed_supply_repository import (
    DismissedSupplyRepository,
)
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)


async def filter_dismissed(
    dismissed: DismissedSupplyRepository, rows: list[RequestRow]
) -> list[RequestRow]:
    """Saca las filas de "pedido activo sin confirmar" (supply_id seteado, order_id
    ausente) cuyo supply_id fue descartado a mano — se filtra por supply_id, no por
    request_id: HP SDS puede reemitir la solicitud con otro ID mientras el pedido viejo
    siga sin resolver."""
    candidates = [n for r in rows if (n := _unconfirmed_supply_num(r)) is not None]
    if not candidates:
        return rows
    dismissed_ids = await dismissed.get_dismissed_ids(candidates)
    if not dismissed_ids:
        return rows
    return [r for r in rows if _unconfirmed_supply_num(r) not in dismissed_ids]


def _unconfirmed_supply_num(row: RequestRow) -> int | None:
    if not row.supply_id or row.order_id:
        return None
    try:
        return int(row.supply_id.split("-")[0])
    except (ValueError, IndexError):
        return None


async def attach_reused_consumable_notes(
    processed: ProcessedRequestRepository, rows: list[RequestRow]
) -> None:
    """Cartucho/drum reinstalado o movido a otro equipo: el consumable_serial de esta
    fila ya generó otro pedido antes. Una sola query batch para toda la página."""
    serials = {r.consumable_serial for r in rows if r.consumable_serial}
    if not serials:
        return
    reuse_by_serial = await processed.find_consumable_serial_reuse_batch(serials)
    for row in rows:
        if not row.consumable_serial:
            continue
        prior = [
            p
            for p in reuse_by_serial.get(row.consumable_serial.upper(), [])
            if p.hp_request_id != row.request_id
        ]
        if not prior:
            continue
        row.reused_consumable_note = _reuse_note(row.consumable_serial, prior[0], row.serial)


def _reuse_note(consumable_serial: str, last: ProcessedRequest, row_serial: str) -> str:
    if last.device_serial.upper() == row_serial.upper():
        return (
            f"Este mismo cartucho/drum (serie {consumable_serial}) ya generó el pedido "
            f"{last.internal_order_id} el {last.created_at} en este equipo — ¿se "
            "reinstaló sin cambiarlo, o es un repuesto usado?"
        )
    return (
        f"Este mismo cartucho/drum (serie {consumable_serial}) ya generó el pedido "
        f"{last.internal_order_id} el {last.created_at} en OTRO equipo "
        f"({last.device_serial}) — ¿se movió de equipo, o es un dato repetido?"
    )
