"""Helpers puros del job de aviso a logística de "solicitud nueva con pedido despachado
sin confirmar entrega" — mismo patrón que pending_order_alert.py. No envían nada: solo
deciden qué avisar y arman el contenido del mail; el job de fondo llama ambas y delega
el envío al mailer."""

from src.modules.insumos.application.dtos.request_rows import RequestRow


def is_unconfirmed_supply_row(row: RequestRow) -> bool:
    """Pedido en Canal Directo detectado por matching (badge en la UI), no un pedido
    propio ya cargado (order_id) — ver dashboard_summary.py / _request_association.py."""
    return bool(row.supply_id) and not row.order_id


def find_dispatch_unconfirmed_due(
    rows: list[RequestRow], already_notified: set[int]
) -> list[RequestRow]:
    return [
        r
        for r in rows
        if is_unconfirmed_supply_row(r) and r.request_id not in already_notified
    ]


def build_dispatch_unconfirmed_mail(rows: list[RequestRow]) -> tuple[str, str]:
    subject = (
        f"[HelpDesk Manager] {len(rows)} solicitud(es) con pedido despachado "
        "sin confirmar entrega"
    )
    lines = [
        "Salió una solicitud nueva de insumo para un equipo que ya tiene un pedido",
        "despachado en Canal Directo sin haber llegado a Entregado (puede ser que el",
        "envío anterior no haya llegado a destino):",
        "",
    ]
    for r in rows:
        cliente = r.customer_name or f"Cliente {r.customer_id}"
        lines.append(
            f"- {cliente} — {r.store or 'sucursal desconocida'} — Serie {r.serial} — "
            f"{r.sku} — Pedido CD {r.supply_id} ({r.supply_status or 'sin estado'}, "
            f"{r.supply_fecha or 'sin fecha'})"
        )
    lines += ["", "Aviso automático — se envía una sola vez por solicitud."]
    return subject, "\n".join(lines)
