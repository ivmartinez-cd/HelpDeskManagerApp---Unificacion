from datetime import UTC, datetime, timedelta

from src.modules.wati.domain.entities.conversacion import ConversacionWati
from src.modules.wati.domain.value_objects.evento import (
    TIPO_MENSAJE,
    TIPO_TICKET,
    ContactoWati,
    EventoWati,
)

T0 = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)


def en(minutos: int) -> datetime:
    return T0 + timedelta(minutes=minutos)


def msg_cliente(minutos: int, texto: str = "hola", operador: str | None = None) -> EventoWati:
    return EventoWati(
        tipo=TIPO_MENSAJE,
        created=en(minutos),
        owner=False,
        es_bot=False,
        texto=texto,
        operador_nombre=operador,
        assignee_email=None,
        descripcion="",
        conversation_id="c1",
        ticket_id="t1",
    )


def msg_operador(minutos: int, operador: str = "MDA Canal Directo") -> EventoWati:
    return EventoWati(
        tipo=TIPO_MENSAJE,
        created=en(minutos),
        owner=True,
        es_bot=False,
        texto="dale",
        operador_nombre=operador,
        assignee_email=None,
        descripcion="",
        conversation_id="c1",
        ticket_id="t1",
    )


def msg_bot(minutos: int) -> EventoWati:
    return EventoWati(
        tipo=TIPO_MENSAJE,
        created=en(minutos),
        owner=True,
        es_bot=True,
        texto="Elegí 1 o 2",
        operador_nombre="Bot",
        assignee_email=None,
        descripcion="",
        conversation_id="c1",
        ticket_id="t1",
    )


def ticket(minutos: int, descripcion: str, assignee: str | None = None) -> EventoWati:
    return EventoWati(
        tipo=TIPO_TICKET,
        created=en(minutos),
        owner=False,
        es_bot=False,
        texto="",
        operador_nombre=None,
        assignee_email=assignee,
        descripcion=descripcion,
        conversation_id="c1",
        ticket_id="t1",
    )


class FakeWatiGateway:
    def __init__(
        self,
        contactos: list[ContactoWati] | None = None,
        eventos: dict[str, list[EventoWati]] | None = None,
    ) -> None:
        self.contactos = contactos or []
        self.eventos = eventos or {}
        self.consultados: list[str] = []

    async def list_contactos_recientes(self, limite: int) -> list[ContactoWati]:
        return self.contactos[:limite]

    async def get_eventos(self, wa_id: str, limite: int) -> list[EventoWati]:
        self.consultados.append(wa_id)
        return self.eventos.get(wa_id, [])[:limite]


class FakeConversacionRepository:
    def __init__(self) -> None:
        self.rows: dict[str, ConversacionWati] = {}

    async def upsert(self, conversacion: ConversacionWati) -> None:
        self.rows[conversacion.wa_id] = conversacion

    async def list_activas(self, desde: datetime) -> list[ConversacionWati]:
        return [
            c
            for c in self.rows.values()
            if (c.ultimo_mensaje_cliente_at is not None and c.ultimo_mensaje_cliente_at >= desde)
            or c.esperando_desde is not None
        ]

    async def list_esperando(self, ahora: datetime) -> list[ConversacionWati]:
        return sorted(
            (c for c in self.rows.values() if c.espera_respuesta(ahora)),
            key=lambda c: c.esperando_desde or ahora,
        )

    async def get_ultima_sincronizacion(self) -> datetime | None:
        return max((c.sincronizado_at for c in self.rows.values()), default=None)
