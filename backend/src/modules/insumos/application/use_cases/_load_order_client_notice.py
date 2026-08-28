"""Aviso de cortesía al cliente cuando LoadOrder carga su pedido — separado de
load_order.py porque ese archivo ya está en el tamaño máximo (guía §4).

Nunca puede hacer fallar la carga (ya confirmada y marcada procesada antes de llamar
acá): cualquier excepción se contiene y se loguea."""

import logging

from src.modules.insumos.application.dtos.load_order import LoadOrderCommand, ResolvedRequest
from src.modules.insumos.application.use_cases._load_order_context import LoadOrderPorts
from src.modules.insumos.domain.value_objects.client_order_notice import (
    ClientOrderNotice,
    resolve_client_recipients,
)
from src.modules.insumos.domain.value_objects.order_request import ContactInfo, OrderRequest

logger = logging.getLogger(__name__)


async def notify_client_order(
    ports: LoadOrderPorts,
    command: LoadOrderCommand,
    resolved: ResolvedRequest,
    order: OrderRequest,
    order_id: str,
) -> None:
    if ports.client_notifier is None:
        return
    if not await ports.customers.is_client_mail_enabled(command.customer_id):
        return
    notice = _build_notice(command, resolved, order, order_id)
    if not notice.to_emails:
        return
    await _send_or_log(ports, notice, order_id, resolved.device_serial)


async def _send_or_log(
    ports: LoadOrderPorts, notice: ClientOrderNotice, order_id: str, device_serial: str
) -> None:
    assert ports.client_notifier is not None
    try:
        await ports.client_notifier.notify(notice)
    except Exception:
        logger.exception(
            "No se pudo avisar por mail al cliente del pedido %s (serie %s)",
            order_id,
            device_serial,
        )


def _build_notice(
    command: LoadOrderCommand, resolved: ResolvedRequest, order: OrderRequest, order_id: str
) -> ClientOrderNotice:
    sol, dest = order.solicitante or ContactInfo(), order.destinatario or ContactInfo()
    return ClientOrderNotice(
        order_id=order_id,
        customer_name=command.customer_name,
        store_name=resolved.store_name,
        sol_nombre=f"{sol.nombre} {sol.apellido}".strip(),
        dest_nombre=f"{dest.nombre} {dest.apellido}".strip(),
        dest_email=dest.email,
        to_emails=resolve_client_recipients(dest.email, sol.email),
    )
