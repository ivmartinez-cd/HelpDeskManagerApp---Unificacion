from dataclasses import dataclass
from datetime import datetime, timedelta

# Ventana de sesión de WhatsApp: pasadas 24 h sin actividad el chat queda
# "Expired" en WATI y ya no se puede responder libremente, así que dejó de
# ser un pendiente accionable.
HORAS_EXPIRACION = 24


@dataclass(frozen=True, slots=True)
class ConversacionWati:
    """Estado derivado de una conversación de WhatsApp: quién espera a quién.
    Se recalcula completa en cada sincronización a partir de los eventos;
    no se versiona."""

    wa_id: str
    nombre: str
    conversation_id: str | None
    ticket_id: str | None
    operador_nombre: str | None
    operador_email: str | None
    ultimo_mensaje_cliente_at: datetime | None
    esperando_desde: datetime | None
    """Primer mensaje del cliente que ningún humano respondió todavía."""
    ultima_respuesta_at: datetime | None
    """Último mensaje de un operador humano (el bot no cuenta)."""
    ultimo_bot_at: datetime | None
    cerrada_at: datetime | None
    bot_activo: bool
    """El chatbot sigue atendiendo (no terminó su flujo ni intervino un humano)."""
    ultimo_texto_cliente: str
    sincronizado_at: datetime

    @property
    def sin_asignar(self) -> bool:
        return not self.operador_email and not self.operador_nombre

    def espera_respuesta(self, ahora: datetime) -> bool:
        if self.esperando_desde is None or self.cerrada_at is not None or self.bot_activo:
            return False
        if self.ultimo_mensaje_cliente_at is None:
            return False
        return ahora - self.ultimo_mensaje_cliente_at <= timedelta(hours=HORAS_EXPIRACION)

    def minutos_esperando(self, ahora: datetime) -> int:
        if self.esperando_desde is None:
            return 0
        return max(0, int((ahora - self.esperando_desde).total_seconds() // 60))
