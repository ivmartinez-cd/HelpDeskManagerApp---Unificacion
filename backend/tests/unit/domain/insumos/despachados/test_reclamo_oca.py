"""Reclamar en OCA: elección del contacto por prefijo de guía y comentario sugerido."""

from dataclasses import replace
from datetime import date

from src.modules.insumos.domain.services.despachados.comentario_reclamo import (
    comentario_reclamo,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import IncidenteInsumo
from src.modules.insumos.domain.value_objects.despachados.reclamo_oca import (
    ContactoReclamoOca,
    ReglaContactoReclamo,
    contacto_para_guia,
)
from tests.unit.application.insumos.despachados.fakes_despachados import (
    VERDE,
    despacho,
    envio,
    estado_oca,
)

CORREO = ContactoReclamoOca("Canal Directo", "SI", "CDSI", "a@x.com", "30709381101", "")
CLIENTE = ContactoReclamoOca("Canal", "Directo", "Canal Directo SA", "b@x.com", "30683465840", "")
REGLAS = (
    ReglaContactoReclamo(prefijo="211", cuenta="443913", contacto=CLIENTE),
    ReglaContactoReclamo(prefijo="26108", cuenta="434324", contacto=CORREO),
)


def test_elige_el_contacto_por_el_prefijo_de_la_guia() -> None:
    assert contacto_para_guia("2610800000000000001", REGLAS) is CORREO
    assert contacto_para_guia("2110000000000000001", REGLAS) is CLIENTE


def test_sin_regla_que_coincida_no_hay_contacto() -> None:
    assert contacto_para_guia("3867500000000000001", REGLAS) is None
    assert contacto_para_guia("2610800000000000001", ()) is None


def test_si_se_solapan_gana_el_prefijo_mas_largo() -> None:
    otro = replace(CLIENTE, email="otro@x.com")
    reglas = (
        ReglaContactoReclamo(prefijo="2", cuenta="corta", contacto=otro),
        *REGLAS,
    )

    assert contacto_para_guia("2110000000000000001", reglas) is CLIENTE
    assert contacto_para_guia("2999000000000000001", reglas) is otro


def test_un_prefijo_vacio_no_coincide_con_todo() -> None:
    reglas = (ReglaContactoReclamo(prefijo="", cuenta="vacía", contacto=CLIENTE),)

    assert contacto_para_guia("2110000000000000001", reglas) is None


def test_comentario_con_estado_motivo_sucursal_cliente_incidentes_y_remitos() -> None:
    estado = estado_oca(estado="Visita fallida", motivo="Domicilio cerrado", id_estado=48)
    remitos = [
        despacho(id_remito=1, bultos=1),
        despacho(
            id_remito=2,
            bultos=3,
            incidentes=(
                IncidenteInsumo(numero="440001", numero_cliente=""),
                IncidenteInsumo(numero="440009", numero_cliente="R-9"),
            ),
        ),
    ]

    texto = comentario_reclamo(envio(estado_oca=estado), remitos)

    assert texto.splitlines() == [
        "Reclamo por el envío 3867500000000000001.",
        "Estado en OCA: Visita fallida (motivo: Domicilio cerrado), desde el 23/09/2026, "
        "sucursal Rosario.",
        "Cliente: Cliente Test (Casa Central).",
        "Incidentes: 440001, 440009.",
        "Remitos: 50001 (1 bulto), 50002 (3 bultos).",
        "Pedimos revisar el envío y confirmar cómo sigue la entrega.",
    ]


def test_comentario_en_rojo_agrega_la_fecha_limite_y_omite_sin_motivo() -> None:
    rojo = replace(VERDE, color=ColorSemaforo.ROJO, alerta=True, fecha_limite=date(2026, 9, 30))
    estado = estado_oca(estado="En Espera de Retiro por Sucursal", id_estado=45)

    texto = comentario_reclamo(envio(clasificacion=rojo, estado_oca=estado), [])

    assert "Sin Motivo" not in texto
    assert "Fecha límite de retiro en sucursal: 30/09/2026." in texto
    assert "Remito" not in texto and "Incidente" not in texto


def test_comentario_de_una_guia_que_oca_todavia_no_registra() -> None:
    texto = comentario_reclamo(envio(sucursal_cliente=""), [despacho()])

    assert "OCA todavía no informa ningún estado para esta guía." in texto
    assert "Cliente: Cliente Test.\nIncidente: 440001.\nRemito: 50001 (1 bulto)." in texto
