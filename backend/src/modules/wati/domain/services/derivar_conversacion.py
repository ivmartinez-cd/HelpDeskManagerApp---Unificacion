"""Regla de negocio central del módulo: a partir de los eventos de un chat
(en cualquier orden) decide si el cliente está esperando respuesta humana.

- Un mensaje del cliente abre la espera (se guarda el PRIMER mensaje sin
  responder, no el último: el tiempo de espera se mide desde que escribió).
- Solo un mensaje de un operador humano cierra la espera; el bot no cuenta.
- Un cierre de ticket sin respuesta también la cierra (no hay nada que
  responder), pero un mensaje posterior la reabre.
- Mientras el chatbot sigue en su flujo (mandó mensajes y no hubo "Ended:"
  ni intervención humana después) no se reclama respuesta humana.
"""

from dataclasses import dataclass
from datetime import datetime

from src.modules.wati.domain.entities.conversacion import ConversacionWati
from src.modules.wati.domain.value_objects.evento import EventoWati

_BOT = "bot"
_MAX_TEXTO = 160


@dataclass
class _Acumulador:
    ultimo_in: datetime | None = None
    esperando_desde: datetime | None = None
    ultima_humana: datetime | None = None
    ultimo_bot: datetime | None = None
    fin_bot: datetime | None = None
    cerrada: datetime | None = None
    operador_nombre: str | None = None
    operador_email: str | None = None
    conversation_id: str | None = None
    ticket_id: str | None = None
    ultimo_texto: str = ""

    def aplicar(self, e: EventoWati) -> None:
        self.conversation_id = e.conversation_id or self.conversation_id
        self.ticket_id = e.ticket_id or self.ticket_id
        if e.es_mensaje:
            self._aplicar_mensaje(e)
        else:
            self._aplicar_ticket(e)

    def _aplicar_mensaje(self, e: EventoWati) -> None:
        self.cerrada = None
        if e.owner and e.es_bot:
            self.ultimo_bot = e.created
            return
        if e.owner:
            self.ultima_humana = e.created
            self.esperando_desde = None
            self._tomar_operador(e.operador_nombre)
            return
        self.ultimo_in = e.created
        self.ultimo_texto = (e.texto or "")[:_MAX_TEXTO]
        if self.esperando_desde is None:
            self.esperando_desde = e.created
        self._tomar_operador(e.operador_nombre)

    def _aplicar_ticket(self, e: EventoWati) -> None:
        if e.es_cierre:
            self.cerrada = e.created
            self.esperando_desde = None
        elif e.es_fin_de_bot:
            self.fin_bot = e.created
        elif e.es_asignacion and e.assignee_email:
            self.operador_email = e.assignee_email

    def _tomar_operador(self, nombre: str | None) -> None:
        if nombre and nombre.strip().lower() != _BOT:
            self.operador_nombre = nombre.strip()

    @property
    def bot_activo(self) -> bool:
        if self.ultimo_bot is None:
            return False
        if self.fin_bot is not None and self.fin_bot >= self.ultimo_bot:
            return False
        return self.ultima_humana is None or self.ultima_humana < self.ultimo_bot


def derivar_conversacion(
    wa_id: str, nombre: str, eventos: list[EventoWati], ahora: datetime
) -> ConversacionWati:
    acum = _Acumulador()
    for evento in sorted(eventos, key=lambda e: e.created):
        acum.aplicar(evento)
    return ConversacionWati(
        wa_id=wa_id,
        nombre=nombre,
        conversation_id=acum.conversation_id,
        ticket_id=acum.ticket_id,
        operador_nombre=acum.operador_nombre,
        operador_email=acum.operador_email,
        ultimo_mensaje_cliente_at=acum.ultimo_in,
        esperando_desde=acum.esperando_desde,
        ultima_respuesta_at=acum.ultima_humana,
        ultimo_bot_at=acum.ultimo_bot,
        cerrada_at=acum.cerrada,
        bot_activo=acum.bot_activo,
        ultimo_texto_cliente=acum.ultimo_texto,
        sincronizado_at=ahora,
    )
