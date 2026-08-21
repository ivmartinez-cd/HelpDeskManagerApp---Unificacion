"""Lo que la API de WATI cuenta de una conversación, ya normalizado: cada
item de `getMessages` es un mensaje (del cliente, de un operador o del bot)
o un evento de ticket (asignación, cierre, fin de chatbot)."""

from dataclasses import dataclass
from datetime import datetime

TIPO_MENSAJE = "message"
TIPO_TICKET = "ticket"


@dataclass(frozen=True, slots=True)
class EventoWati:
    tipo: str
    created: datetime
    """Siempre aware en UTC."""
    owner: bool
    """True si lo mandó el negocio (operador humano o bot); False si el cliente."""
    es_bot: bool
    texto: str
    operador_nombre: str | None
    """En mensajes, el operador asignado a la conversación en ese momento
    (WATI lo informa también en los mensajes del cliente)."""
    assignee_email: str | None
    """Solo en eventos de ticket "Chat is now assigned to ..."."""
    descripcion: str
    """`eventDescription` de los eventos de ticket; vacío en mensajes."""
    conversation_id: str | None
    ticket_id: str | None

    @property
    def es_mensaje(self) -> bool:
        return self.tipo == TIPO_MENSAJE

    @property
    def es_cierre(self) -> bool:
        return self.tipo == TIPO_TICKET and "closed" in self.descripcion.lower()

    @property
    def es_fin_de_bot(self) -> bool:
        return self.tipo == TIPO_TICKET and self.descripcion.lower().startswith("ended:")

    @property
    def es_asignacion(self) -> bool:
        return self.tipo == TIPO_TICKET and "assigned to" in self.descripcion.lower()


@dataclass(frozen=True, slots=True)
class ContactoWati:
    wa_id: str
    nombre: str
    last_updated: datetime
    """Marca el inicio de la última conversación / corrida del bot — NO el
    último mensaje (verificado contra la API el 2026-08-21)."""
