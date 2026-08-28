"""Aviso al cliente cuando la app carga un pedido de insumos (mail vía SMTP).

Los pedidos se crean por SOAP (persistNewSupply) y ese camino no dispara ningún mail de
Canal Directo al cliente, a diferencia de cargar por el portal WebAgentes/WebClientes —
esto reemplaza ese aviso. Clona el formato exacto del mail real de Canal Directo (mismos
campos: Sucursal, Solicitante, Entrega a, E-mail, link), salvo la "Dirección" postal de
la sucursal: no está disponible en este flujo (ver zone_delivery_notice.py).

Puro (arma texto, no envía) para que sea fácil de testear, mismo patrón que
pending_order_alert.py."""

import re
from dataclasses import dataclass

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class ClientOrderNotice:
    order_id: str
    customer_name: str
    store_name: str
    sol_nombre: str
    dest_nombre: str
    dest_email: str
    to_emails: list[str]


def resolve_client_recipients(dest_email: str | None, sol_email: str | None) -> list[str]:
    """Destinatario + solicitante del pedido, normalizados, deduplicados (suelen
    coincidir) y filtrados por formato válido. Sin ninguno válido: []."""
    candidates = [(dest_email or "").strip().lower(), (sol_email or "").strip().lower()]
    seen: set[str] = set()
    result: list[str] = []
    for email in candidates:
        if email and email not in seen and _EMAIL_RE.match(email):
            seen.add(email)
            result.append(email)
    return result


def build_client_order_mail(notice: ClientOrderNotice, clientes_base_url: str) -> tuple[str, str]:
    """Devuelve (subject, text). El original de Canal Directo es texto plano (por eso los
    campos se alinean parejo, sin negritas ni colores) — se manda igual, sin HTML, para
    que el resultado sea indistinguible del mail que ya conocen los clientes."""
    subject = f"Solicitud de Insumos Nro.: {notice.order_id} - {notice.customer_name}"
    return subject, _body_text(notice, f"{clientes_base_url}/supplies/view/{notice.order_id}")


def _body_text(notice: ClientOrderNotice, detail_url: str) -> str:
    text_lines = [
        "CANAL DIRECTO",
        "",
        f"Solicitud de Insumos No.: {notice.order_id}",
        "",
        f"Sucursal:     {notice.store_name or '-'}",
        "",
        f"Solicitante:  {notice.sol_nombre or '-'}",
        f"Entrega a:    {notice.dest_nombre or '-'}",
        f"E-mail:       {notice.dest_email or '-'}",
        "",
        "Ingrese al siguiente link para más detalles:",
        detail_url,
    ]
    return "\n".join(text_lines)
