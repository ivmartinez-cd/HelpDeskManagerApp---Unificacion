"""Tests del paso del tiempo en el semáforo de Despachados: días sin movimiento, plazo de
retiro del rojo (5 días hábiles desde `FechaEstado`) y guías que OCA todavía no registra."""

from dataclasses import replace
from datetime import date

import pytest

from src.modules.insumos.domain.services.despachados.semaforo import (
    clasificar_estado,
    clasificar_sin_datos,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import (
    ClasificacionEnvio,
    ContextoClasificacion,
)
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca
from tests.unit.domain.insumos.despachados.datos_semaforo import (
    AMARILLO,
    EN_ESPERA,
    EN_VIAJE,
    FERIADO_12_OCT,
    GRIS_ABIERTO,
    LUNES_21_SEP,
    NARANJA,
    OTRO_TEXTO,
    ROJO_LIMITE_25_SEP,
    VERDE,
    VIERNES_9_OCT,
    VIERNES_30_OCT,
    con_fecha,
    contexto_en,
    estado_oca,
)


@pytest.mark.parametrize(
    ("fecha_estado", "hoy", "esperado"),
    [
        pytest.param(LUNES_21_SEP, date(2026, 9, 23), VERDE, id="2-dias-verde"),
        pytest.param(
            LUNES_21_SEP,
            date(2026, 9, 24),
            replace(AMARILLO, observacion="Sin movimiento hace 3 días hábiles"),
            id="3-dias-amarillo",
        ),
        pytest.param(date(2026, 9, 25), date(2026, 9, 28), VERDE, id="viernes-a-lunes-es-1-dia"),
    ],
)
def test_sin_movimiento_en_el_borde(
    fecha_estado: date, hoy: date, esperado: ClasificacionEnvio
) -> None:
    """Con `dias_sin_movimiento=3`: 2 días hábiles sin cambios es verde, 3 es amarillo."""
    estado = con_fecha(estado_oca(10, EN_VIAJE, "Sin Motivo"), fecha_estado)

    assert clasificar_estado(estado, contexto_en(hoy)) == esperado


def test_sin_movimiento_en_singular() -> None:
    contexto = ContextoClasificacion(
        hoy=date(2026, 9, 22), feriados=frozenset(), dias_sin_movimiento=1
    )

    clasificacion = clasificar_estado(estado_oca(1, OTRO_TEXTO, "Sin Motivo"), contexto)

    assert clasificacion == replace(AMARILLO, observacion="Sin movimiento hace 1 día hábil")


def test_sin_movimiento_no_cuenta_feriados() -> None:
    estado = con_fecha(estado_oca(10, EN_VIAJE, "Sin Motivo"), VIERNES_9_OCT)

    clasificacion = clasificar_estado(estado, contexto_en(date(2026, 10, 14), FERIADO_12_OCT))

    assert clasificacion == VERDE  # 13 y 14 de octubre: 2 días hábiles


@pytest.mark.parametrize(
    ("estado", "esperado"),
    [
        pytest.param(estado_oca(45, EN_ESPERA, "Sin Motivo"), ROJO_LIMITE_25_SEP, id="45-rojo"),
        pytest.param(
            estado_oca(48, "Reprogramado para nueva visita", "No Responde"),
            NARANJA,
            id="48-naranja",
        ),
        pytest.param(estado_oca(10, EN_VIAJE, "No Responde"), NARANJA, id="10-con-motivo"),
        pytest.param(estado_oca(49, OTRO_TEXTO, "Sin Motivo"), GRIS_ABIERTO, id="49-gris-abierto"),
    ],
)
def test_sin_movimiento_solo_pasa_a_amarillo_a_los_verdes(
    estado: EstadoOca, esperado: ClasificacionEnvio
) -> None:
    """Rojo, naranja y gris abierto no cambian de color aunque `FechaEstado` no se mueva."""
    assert clasificar_estado(estado, contexto_en(VIERNES_30_OCT)) == esperado


@pytest.mark.parametrize(
    "hoy",
    [
        pytest.param(date(2026, 9, 24), id="3-dias-habiles-despues"),
        pytest.param(date(2026, 9, 25), id="el-dia-limite"),
        pytest.param(date(2026, 9, 30), id="limite-vencido"),
    ],
)
def test_limite_de_retiro_se_cuenta_desde_fechaestado_oca(hoy: date) -> None:
    """El job corre varias veces por día: el límite no se corre con `hoy` ni pasa a amarillo."""
    estado = estado_oca(45, EN_ESPERA, "Sin Motivo")

    assert clasificar_estado(estado, contexto_en(hoy)) == ROJO_LIMITE_25_SEP


def test_limite_de_retiro_cruza_feriado_aunque_hoy_sea_posterior() -> None:
    estado = con_fecha(estado_oca(45, EN_ESPERA, "Sin Motivo"), VIERNES_9_OCT)

    clasificacion = clasificar_estado(estado, contexto_en(date(2026, 10, 14), FERIADO_12_OCT))

    assert clasificacion.fecha_limite == date(2026, 10, 16)


def test_rojo_con_ingreso_en_fin_de_semana() -> None:
    """Ingresó el sábado 26/09: el día 1 es el lunes 28/09 y el límite el viernes 02/10."""
    estado = con_fecha(estado_oca(45, EN_ESPERA, "Sin Motivo"), date(2026, 9, 26))

    clasificacion = clasificar_estado(estado, contexto_en(date(2026, 9, 26)))

    assert clasificacion == replace(ROJO_LIMITE_25_SEP, fecha_limite=date(2026, 10, 2))


@pytest.mark.parametrize(
    ("hoy", "esperado"),
    [
        pytest.param(
            date(2026, 9, 23),
            replace(VERDE, observacion="Esperando ingreso en OCA"),
            id="antes-del-umbral",
        ),
        pytest.param(
            date(2026, 9, 24),
            replace(AMARILLO, observacion="Sin datos en OCA"),
            id="en-el-umbral",
        ),
        pytest.param(
            VIERNES_30_OCT,
            replace(AMARILLO, observacion="Sin datos en OCA"),
            id="despues-del-umbral",
        ),
    ],
)
def test_clasificar_sin_datos(hoy: date, esperado: ClasificacionEnvio) -> None:
    assert clasificar_sin_datos(LUNES_21_SEP, contexto_en(hoy)) == esperado
