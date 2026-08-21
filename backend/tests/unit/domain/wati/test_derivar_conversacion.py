from datetime import timedelta

from src.modules.wati.domain.services.derivar_conversacion import derivar_conversacion
from tests.unit.domain.wati.fakes import (
    en,
    msg_bot,
    msg_cliente,
    msg_operador,
    ticket,
)

AHORA = en(60)


def _derivar(eventos: list) -> object:  # type: ignore[type-arg]
    return derivar_conversacion("549111", "Cliente", eventos, AHORA)


def test_cliente_escribe_y_nadie_responde_espera_desde_el_primer_mensaje() -> None:
    conv = _derivar([msg_cliente(10, "hola"), msg_cliente(20, "sigo acá")])

    assert conv.espera_respuesta(AHORA)
    assert conv.esperando_desde == en(10)
    assert conv.ultimo_mensaje_cliente_at == en(20)
    assert conv.ultimo_texto_cliente == "sigo acá"
    assert conv.minutos_esperando(AHORA) == 50


def test_respuesta_humana_cierra_la_espera() -> None:
    conv = _derivar([msg_cliente(10), msg_operador(15)])

    assert not conv.espera_respuesta(AHORA)
    assert conv.esperando_desde is None
    assert conv.ultima_respuesta_at == en(15)
    assert conv.operador_nombre == "MDA Canal Directo"


def test_cliente_vuelve_a_escribir_despues_de_la_respuesta_reabre_la_espera() -> None:
    conv = _derivar([msg_cliente(10), msg_operador(15), msg_cliente(30)])

    assert conv.espera_respuesta(AHORA)
    assert conv.esperando_desde == en(30)


def test_el_orden_de_llegada_de_los_eventos_no_importa() -> None:
    eventos = [msg_cliente(30), msg_operador(15), msg_cliente(10)]

    conv = _derivar(eventos)

    assert conv.esperando_desde == en(30)


def test_el_bot_no_cuenta_como_respuesta_una_vez_que_termino_su_flujo() -> None:
    eventos = [
        msg_bot(0),
        msg_cliente(1, "1"),
        msg_bot(2),
        msg_cliente(3, "2"),
        ticket(4, "Ended: Chatbot Laboral by DefaultAction"),
        ticket(4, "Chat is now assigned to mda@canaldirecto.com.ar", "mda@canaldirecto.com.ar"),
    ]

    conv = _derivar(eventos)

    assert not conv.bot_activo
    assert conv.espera_respuesta(AHORA)
    assert conv.operador_email == "mda@canaldirecto.com.ar"


def test_mientras_el_bot_sigue_atendiendo_no_se_reclama_respuesta_humana() -> None:
    conv = _derivar([msg_cliente(0, "hola"), msg_bot(1), msg_cliente(2, "1"), msg_bot(3)])

    assert conv.bot_activo
    assert not conv.espera_respuesta(AHORA)


def test_cierre_sin_respuesta_no_queda_pendiente() -> None:
    conv = _derivar([msg_cliente(10), ticket(20, "The chat has been closed by agent MDA")])

    assert conv.cerrada_at == en(20)
    assert not conv.espera_respuesta(AHORA)


def test_mensaje_posterior_al_cierre_reabre() -> None:
    eventos = [
        msg_cliente(10),
        msg_operador(12),
        ticket(20, "The chat has been closed by agent MDA"),
        msg_cliente(40, "otra cosa"),
    ]

    conv = _derivar(eventos)

    assert conv.cerrada_at is None
    assert conv.espera_respuesta(AHORA)
    assert conv.esperando_desde == en(40)


def test_pasadas_24h_la_sesion_expiro_y_deja_de_ser_pendiente() -> None:
    conv = _derivar([msg_cliente(0)])

    assert conv.espera_respuesta(en(0) + timedelta(hours=23))
    assert not conv.espera_respuesta(en(0) + timedelta(hours=25))


def test_operador_asignado_se_toma_del_mensaje_del_cliente_si_no_hubo_respuesta() -> None:
    conv = _derivar([msg_cliente(10, operador="Soporte Digital Signage")])

    assert conv.operador_nombre == "Soporte Digital Signage"
    assert not conv.sin_asignar


def test_sin_operador_ni_email_queda_sin_asignar() -> None:
    conv = _derivar([msg_cliente(10, operador="Bot")])

    assert conv.sin_asignar


def test_sin_eventos_no_hay_nada_pendiente() -> None:
    conv = _derivar([])

    assert not conv.espera_respuesta(AHORA)
    assert conv.minutos_esperando(AHORA) == 0
