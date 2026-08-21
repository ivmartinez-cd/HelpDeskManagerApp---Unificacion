"""Del JSON de la API V1 de WATI a los value objects del dominio.
Campos verificados contra la API real el 2026-08-21 (ver memoria del
proyecto): `getContacts` → contact_list[{wAid, fullName, firstName,
lastUpdated}], `getMessages` → messages.items[{eventType, owner,
operatorName, created, text, eventDescription, assignee, conversationId,
ticketId}]. Timestamps ISO 8601 en UTC con sufijo Z."""

from datetime import UTC, datetime
from typing import Any

from src.modules.wati.domain.value_objects.evento import (
    TIPO_MENSAJE,
    TIPO_TICKET,
    ContactoWati,
    EventoWati,
)

_BOT = "bot"


def parse_fecha(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _str(raw: object) -> str | None:
    return raw.strip() if isinstance(raw, str) and raw.strip() else None


def contacto_from_json(d: dict[str, Any]) -> ContactoWati | None:
    wa_id = _str(d.get("wAid")) or _str(d.get("phone"))
    last_updated = parse_fecha(d.get("lastUpdated"))
    if wa_id is None or last_updated is None:
        return None
    nombre = _str(d.get("fullName")) or _str(d.get("firstName")) or wa_id
    return ContactoWati(wa_id=wa_id, nombre=nombre, last_updated=last_updated)


def evento_from_json(d: dict[str, Any]) -> EventoWati | None:
    tipo = _str(d.get("eventType"))
    created = parse_fecha(d.get("created"))
    if tipo not in (TIPO_MENSAJE, TIPO_TICKET) or created is None:
        return None
    operador = _str(d.get("operatorName"))
    return EventoWati(
        tipo=tipo,
        created=created,
        owner=bool(d.get("owner")),
        es_bot=(operador or "").lower() == _BOT,
        texto=_str(d.get("text")) or "",
        operador_nombre=operador,
        assignee_email=_str(d.get("assignee")),
        descripcion=_str(d.get("eventDescription")) or "",
        conversation_id=_str(d.get("conversationId")),
        ticket_id=_str(d.get("ticketId")),
    )
