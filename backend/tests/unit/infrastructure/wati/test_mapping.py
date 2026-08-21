from datetime import UTC, datetime

from src.modules.wati.infrastructure.wati_api.mapping import (
    contacto_from_json,
    evento_from_json,
    parse_fecha,
)


def test_parse_fecha_iso_con_z_queda_aware_utc() -> None:
    assert parse_fecha("2026-08-21T14:02:01.919Z") == datetime(
        2026, 8, 21, 14, 2, 1, 919000, tzinfo=UTC
    )
    assert parse_fecha(None) is None
    assert parse_fecha("Aug-21-2026") is None


def test_contacto_usa_fullname_y_cae_al_numero() -> None:
    c = contacto_from_json(
        {"wAid": "5491130648978", "fullName": "Tienda 0649", "lastUpdated": "2026-08-21T13:27:04Z"}
    )
    assert c is not None
    assert (c.wa_id, c.nombre) == ("5491130648978", "Tienda 0649")

    sin_nombre = contacto_from_json(
        {"wAid": "549", "fullName": None, "lastUpdated": "2026-08-21T13:27:04Z"}
    )
    assert sin_nombre is not None and sin_nombre.nombre == "549"
    assert contacto_from_json({"wAid": "549"}) is None


def test_evento_mensaje_del_cliente_y_del_bot() -> None:
    cliente = evento_from_json(
        {
            "eventType": "message",
            "owner": False,
            "operatorName": "MDA Canal Directo",
            "created": "2026-08-21T15:57:06.587Z",
            "text": "sigue sin enviar",
            "conversationId": "c1",
            "ticketId": "t1",
        }
    )
    assert cliente is not None
    assert not cliente.owner and not cliente.es_bot
    assert cliente.operador_nombre == "MDA Canal Directo"
    assert cliente.texto == "sigue sin enviar"

    bot = evento_from_json(
        {
            "eventType": "message",
            "owner": True,
            "operatorName": "Bot ",
            "created": "2026-08-21T12:06:20Z",
        }
    )
    assert bot is not None and bot.es_bot


def test_eventos_de_ticket_asignacion_y_cierre() -> None:
    asignado = evento_from_json(
        {
            "eventType": "ticket",
            "created": "2026-08-21T12:33:24Z",
            "eventDescription": "Chat is now assigned to mda@canaldirecto.com.ar. A",
            "assignee": "mda@canaldirecto.com.ar",
        }
    )
    cerrado = evento_from_json(
        {
            "eventType": "ticket",
            "created": "2026-08-21T14:25:35Z",
            "eventDescription": "The chat has been closed by agent MDA (mda@canaldirecto.com.ar)",
        }
    )
    assert asignado is not None and asignado.es_asignacion
    assert asignado.assignee_email == "mda@canaldirecto.com.ar"
    assert cerrado is not None and cerrado.es_cierre
    assert evento_from_json({"eventType": "call", "created": "2026-08-21T12:00:00Z"}) is None
