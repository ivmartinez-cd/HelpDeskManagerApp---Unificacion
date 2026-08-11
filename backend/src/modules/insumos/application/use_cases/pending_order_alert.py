"""Helpers puros del job de aviso de pedidos por vencer.

No envían nada: solo deciden qué avisar (`find_orders_due_for_alert`) y arman
el contenido del mail (`build_pending_alert_mail`). El job de fondo llama ambas
funciones y delega el envío al mailer.
"""

from src.modules.insumos.application.dtos.pending_orders import PendingOrderRow
from src.modules.insumos.domain.value_objects.cd_state import PENDIENTE


def find_orders_due_for_alert(
    rows: list[PendingOrderRow],
    threshold_days: int,
    already_notified: set[int],
) -> list[PendingOrderRow]:
    """Pedidos que necesitan el mail de "por vencer, dar curso".

    Solo estado Pendiente: Remito Generado y Despachado ya están en movimiento
    en Canal Directo, nadie tiene que darles curso a mano. Sin `current_days_left`
    no se avisa (sin ese dato no hay forma de saber si vence).
    """
    return [
        r
        for r in rows
        if r.supply_status == PENDIENTE
        and r.current_days_left is not None
        and r.current_days_left <= threshold_days
        and r.hp_request_id not in already_notified
    ]


def build_pending_alert_mail(
    rows: list[PendingOrderRow], threshold_days: int
) -> tuple[str, str]:
    """(subject, body) del mail a logística — texto plano, no HTML."""
    subject = (
        f"[HelpDesk Manager] {len(rows)} pedido(s) Pendiente(s) por vencer"
        " — dar curso en Canal Directo"
    )
    lines = [
        f"Los siguientes pedidos llegaron a {threshold_days} día(s) o menos de",
        "insumo restante y siguen Pendiente en Canal Directo (sin Remito Generado):",
        "",
    ]
    for r in rows:
        cliente = r.customer_name or f"Cliente {r.customer_id}"
        lines.append(
            f"- {cliente} — {r.store or 'sucursal desconocida'} — "
            f"Serie {r.serial} — {r.sku} — "
            f"{r.current_days_left} día(s) restantes — Pedido CD {r.order_id}"
        )
        if r.supply_url:
            lines.append(f"  {r.supply_url}")
    lines += ["", "Aviso automático — se envía una sola vez por pedido."]
    return subject, "\n".join(lines)
