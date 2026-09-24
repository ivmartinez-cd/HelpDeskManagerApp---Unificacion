"""Tests de las reglas del semáforo de Despachados (color, alerta, cierre y observación).

Salvo en los casos que prueban el paso del tiempo (sin movimiento, plazo del rojo; la
mayoría en `test_semaforo_plazos.py`), `hoy` es la misma `FechaEstado`, para que la falta de
movimiento no interfiera con la regla que se prueba.
"""

from dataclasses import replace
from datetime import date

import pytest

from src.modules.insumos.domain.services.despachados.semaforo import (
    clasificar_estado,
    normalizar_texto,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import (
    ClasificacionEnvio,
    ColorSemaforo,
    ContextoClasificacion,
)
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca
from tests.unit.domain.insumos.despachados.datos_semaforo import (
    AMARILLO,
    CERRADO,
    EN_ESPERA,
    EN_VIAJE,
    ESTADO_NUEVO,
    FERIADO_12_OCT,
    GRIS_ABIERTO,
    GRIS_CERRADO,
    LUNES_21_SEP,
    NARANJA,
    OTRO_TEXTO,
    ROJO_LIMITE_25_SEP,
    VERDE,
    VERDES_DEL_CATALOGO,
    VIERNES_9_OCT,
    con_fecha,
    contexto_en,
    estado_oca,
)

CASOS_DEL_BRIEF = [
    pytest.param(
        estado_oca(48, "Reprogramado para nueva visita", "No Responde"),
        contexto_en(LUNES_21_SEP),
        NARANJA,
        id="48-reprogramado-no-responde",
    ),
    pytest.param(
        estado_oca(35, "Programado para visita a domicilio", "Domicilio Incompleto"),
        contexto_en(LUNES_21_SEP),
        NARANJA,
        id="35-con-motivo",
    ),
    pytest.param(
        estado_oca(35, "Programado para visita a domicilio", "Sin Motivo"),
        contexto_en(LUNES_21_SEP),
        VERDE,
        id="35-sin-motivo",
    ),
    pytest.param(
        estado_oca(45, EN_ESPERA, "Sin Motivo"),
        contexto_en(LUNES_21_SEP),
        replace(VERDE, color=ColorSemaforo.ROJO, alerta=True, fecha_limite=date(2026, 9, 25)),
        id="45-en-espera-lunes",
    ),
    pytest.param(
        con_fecha(estado_oca(45, EN_ESPERA, "Sin Motivo"), VIERNES_9_OCT),
        contexto_en(VIERNES_9_OCT, FERIADO_12_OCT),
        replace(VERDE, color=ColorSemaforo.ROJO, alerta=True, fecha_limite=date(2026, 10, 16)),
        id="45-en-espera-antes-de-feriado",
    ),
    pytest.param(
        estado_oca(13, "Devuelto al Remitente", "Rechazado"),
        contexto_en(LUNES_21_SEP),
        GRIS_CERRADO,
        id="13-devuelto",
    ),
    pytest.param(
        estado_oca(None, "Rendicion de Acuse Finalizado", "Sin Motivo"),
        contexto_en(LUNES_21_SEP),
        CERRADO,
        id="acuse-sin-id",
    ),
    pytest.param(
        estado_oca(8, "Entregado", "Sin Motivo"),
        contexto_en(LUNES_21_SEP),
        CERRADO,
        id="8-entregado",
    ),
    pytest.param(
        estado_oca(10, EN_VIAJE, "Sin Motivo"),
        contexto_en(date(2026, 9, 25)),
        replace(AMARILLO, observacion="Sin movimiento hace 4 días hábiles"),
        id="10-sin-movimiento-4-dias",
    ),
    pytest.param(
        estado_oca(99, "texto nuevo", "Sin Motivo"),
        contexto_en(LUNES_21_SEP),
        ESTADO_NUEVO,
        id="99-estado-nuevo",
    ),
]


@pytest.mark.parametrize(("estado", "contexto", "esperado"), CASOS_DEL_BRIEF)
def test_casos_del_brief(
    estado: EstadoOca, contexto: ContextoClasificacion, esperado: ClasificacionEnvio
) -> None:
    assert clasificar_estado(estado, contexto) == esperado


@pytest.mark.parametrize(
    ("estado", "esperado"),
    [
        pytest.param(
            estado_oca(45, EN_ESPERA, "Domicilio Incompleto"),
            ROJO_LIMITE_25_SEP,
            id="45-con-motivo-sigue-rojo",
        ),
        pytest.param(
            estado_oca(13, "Devuelto al Remitente", "No Responde"), GRIS_CERRADO, id="13-con-motivo"
        ),
        pytest.param(estado_oca(49, OTRO_TEXTO, "No Responde"), NARANJA, id="49-con-motivo"),
        pytest.param(estado_oca(8, "Entregado", "Rechazado"), CERRADO, id="8-con-motivo"),
    ],
)
def test_precedencia_entre_reglas(estado: EstadoOca, esperado: ClasificacionEnvio) -> None:
    assert clasificar_estado(estado, contexto_en(LUNES_21_SEP)) == esperado


@pytest.mark.parametrize(
    ("id_estado", "esperado"),
    [
        *(
            pytest.param(id_verde, VERDE, id=f"{id_verde}-verde")
            for id_verde in VERDES_DEL_CATALOGO
        ),
        pytest.param(48, NARANJA, id="48-naranja"),
        pytest.param(45, ROJO_LIMITE_25_SEP, id="45-rojo"),
        pytest.param(13, GRIS_CERRADO, id="13-gris-cerrado"),
        pytest.param(49, GRIS_ABIERTO, id="49-gris-abierto"),
        pytest.param(8, CERRADO, id="8-cerrado"),
        pytest.param(56, CERRADO, id="56-cerrado"),
    ],
)
def test_catalogo_sin_motivo(id_estado: int, esperado: ClasificacionEnvio) -> None:
    """Cada `IdEstado` relevado: uno que falte o esté mal tipeado saldría "Estado nuevo"."""
    estado = estado_oca(id_estado, OTRO_TEXTO, "Sin Motivo")

    assert clasificar_estado(estado, contexto_en(LUNES_21_SEP)) == esperado


@pytest.mark.parametrize("id_estado", VERDES_DEL_CATALOGO)
def test_todo_verde_con_motivo_pasa_a_naranja(id_estado: int) -> None:
    estado = estado_oca(id_estado, OTRO_TEXTO, "No Responde")

    assert clasificar_estado(estado, contexto_en(LUNES_21_SEP)) == NARANJA


def test_estado_nuevo_con_motivo_es_naranja_y_se_marca_desconocido() -> None:
    estado = estado_oca(99, "texto nuevo", "No Responde")

    clasificacion = clasificar_estado(estado, contexto_en(LUNES_21_SEP))

    assert clasificacion == replace(
        NARANJA, observacion="Estado nuevo, revisar", estado_desconocido=True
    )


def test_texto_sin_id_estado_que_no_es_acuse_es_estado_nuevo() -> None:
    estado = estado_oca(None, "Otro estado sin id", "Sin Motivo")

    assert clasificar_estado(estado, contexto_en(LUNES_21_SEP)) == ESTADO_NUEVO


def test_estado_nuevo_no_espera_dias_sin_movimiento() -> None:
    estado = estado_oca(99, "texto nuevo", "Sin Motivo")

    assert clasificar_estado(estado, contexto_en(date(2026, 10, 30))) == ESTADO_NUEVO


@pytest.mark.parametrize(
    "texto",
    [
        "Acuse en Rendición",
        "  ACUSE   EN   RENDICION  ",
        "envío a rendir a otra suc",
        "Rendición de Acuse Finalizado\t",
    ],
)
def test_acuses_se_reconocen_con_texto_normalizado(texto: str) -> None:
    estado = estado_oca(None, texto, "Sin Motivo")

    assert clasificar_estado(estado, contexto_en(LUNES_21_SEP)) == CERRADO


@pytest.mark.parametrize("motivo", ["", "   ", "sin motivo", "  SIN   Motivo ", "Sin Motívo"])
def test_sin_motivo_normalizado_o_vacio_no_es_motivo(motivo: str) -> None:
    estado = estado_oca(35, "Programado para visita a domicilio", motivo)

    assert clasificar_estado(estado, contexto_en(LUNES_21_SEP)) == VERDE


def test_normalizar_texto() -> None:
    assert normalizar_texto("  Envío   a Rendir\ta OTRA Suc ") == "envio a rendir a otra suc"


def test_texto_de_acuse_con_id_estado_no_cierra_el_envio() -> None:
    """El acuse se reconoce por texto solo cuando OCA no manda `IdEstado`: con un id
    desconocido, manda el id y el envío queda para revisar."""
    estado = estado_oca(99, "Acuse en Rendicion", "Sin Motivo")

    assert clasificar_estado(estado, contexto_en(LUNES_21_SEP)) == ESTADO_NUEVO
