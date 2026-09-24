"""Tests de las reglas del semáforo de Despachados (color, alerta, cierre y observación).

Salvo en los casos que prueban el paso del tiempo (sin movimiento, plazo del rojo), `hoy` es
la misma `FechaEstado`, para que la falta de movimiento no interfiera con la regla que se
prueba.
"""

from dataclasses import replace
from datetime import date

import pytest

from src.modules.insumos.domain.services.despachados.semaforo import (
    clasificar_estado,
    clasificar_sin_datos,
    normalizar_texto,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import (
    ClasificacionEnvio,
    ColorSemaforo,
    ContextoClasificacion,
)
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca

LUNES_21_SEP = date(2026, 9, 21)
VIERNES_9_OCT = date(2026, 10, 9)
VIERNES_30_OCT = date(2026, 10, 30)
"""29 días hábiles después del 21/09: muy por encima de cualquier umbral de sin movimiento."""
FERIADO_12_OCT = frozenset({date(2026, 10, 12)})
EN_VIAJE = "En viaje a Centro de Distribución de Destino"
EN_ESPERA = "En Espera de Retiro por Sucursal"
OTRO_TEXTO = "texto de OCA"
"""Para los casos en que la regla mira solo `IdEstado`."""

VERDE = ClasificacionEnvio(
    color=ColorSemaforo.VERDE,
    alerta=False,
    abierto=True,
    fecha_limite=None,
    observacion="",
    estado_desconocido=False,
)
NARANJA = replace(VERDE, color=ColorSemaforo.NARANJA, alerta=True)
GRIS_ABIERTO = replace(VERDE, color=ColorSemaforo.GRIS)
GRIS_CERRADO = replace(VERDE, color=ColorSemaforo.GRIS, abierto=False)
CERRADO = replace(VERDE, color=ColorSemaforo.CERRADO, abierto=False)
AMARILLO = replace(VERDE, color=ColorSemaforo.AMARILLO)
ESTADO_NUEVO = replace(AMARILLO, observacion="Estado nuevo, revisar", estado_desconocido=True)
ROJO_LIMITE_25_SEP = replace(
    VERDE, color=ColorSemaforo.ROJO, alerta=True, fecha_limite=date(2026, 9, 25)
)
"""Rojo de un 45 con `FechaEstado` el lunes 21/09/2026."""
VERDES_DEL_CATALOGO = (1, 44, 34, 10, 2, 4, 35)
"""Escritos a mano, no importados de `semaforo`: así el test fija el catálogo."""


def _estado(id_estado: int | None, texto: str, motivo: str) -> EstadoOca:
    """Envío a domicilio con `FechaEstado` el lunes 21/09/2026."""
    return EstadoOca(
        numero_envio="3867500000000123456",
        operativa="434324",
        orden_retiro="",
        sucursal_actual="",
        fecha_estado=LUNES_21_SEP,
        estado=texto,
        id_estado=id_estado,
        motivo=motivo,
        cantidad_paquetes=1,
    )


def _con_fecha(estado: EstadoOca, fecha_estado: date) -> EstadoOca:
    return replace(estado, fecha_estado=fecha_estado)


def _contexto(hoy: date, feriados: frozenset[date] = frozenset()) -> ContextoClasificacion:
    return ContextoClasificacion(hoy=hoy, feriados=feriados)


CASOS_DEL_BRIEF = [
    pytest.param(
        _estado(48, "Reprogramado para nueva visita", "No Responde"),
        _contexto(LUNES_21_SEP),
        NARANJA,
        id="48-reprogramado-no-responde",
    ),
    pytest.param(
        _estado(35, "Programado para visita a domicilio", "Domicilio Incompleto"),
        _contexto(LUNES_21_SEP),
        NARANJA,
        id="35-con-motivo",
    ),
    pytest.param(
        _estado(35, "Programado para visita a domicilio", "Sin Motivo"),
        _contexto(LUNES_21_SEP),
        VERDE,
        id="35-sin-motivo",
    ),
    pytest.param(
        _estado(45, EN_ESPERA, "Sin Motivo"),
        _contexto(LUNES_21_SEP),
        replace(VERDE, color=ColorSemaforo.ROJO, alerta=True, fecha_limite=date(2026, 9, 25)),
        id="45-en-espera-lunes",
    ),
    pytest.param(
        _con_fecha(_estado(45, EN_ESPERA, "Sin Motivo"), VIERNES_9_OCT),
        _contexto(VIERNES_9_OCT, FERIADO_12_OCT),
        replace(VERDE, color=ColorSemaforo.ROJO, alerta=True, fecha_limite=date(2026, 10, 16)),
        id="45-en-espera-antes-de-feriado",
    ),
    pytest.param(
        _estado(13, "Devuelto al Remitente", "Rechazado"),
        _contexto(LUNES_21_SEP),
        GRIS_CERRADO,
        id="13-devuelto",
    ),
    pytest.param(
        _estado(None, "Rendicion de Acuse Finalizado", "Sin Motivo"),
        _contexto(LUNES_21_SEP),
        CERRADO,
        id="acuse-sin-id",
    ),
    pytest.param(
        _estado(8, "Entregado", "Sin Motivo"),
        _contexto(LUNES_21_SEP),
        CERRADO,
        id="8-entregado",
    ),
    pytest.param(
        _estado(10, EN_VIAJE, "Sin Motivo"),
        _contexto(date(2026, 9, 25)),
        replace(AMARILLO, observacion="Sin movimiento hace 4 días hábiles"),
        id="10-sin-movimiento-4-dias",
    ),
    pytest.param(
        _estado(99, "texto nuevo", "Sin Motivo"),
        _contexto(LUNES_21_SEP),
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
            _estado(45, EN_ESPERA, "Domicilio Incompleto"),
            ROJO_LIMITE_25_SEP,
            id="45-con-motivo-sigue-rojo",
        ),
        pytest.param(
            _estado(13, "Devuelto al Remitente", "No Responde"), GRIS_CERRADO, id="13-con-motivo"
        ),
        pytest.param(_estado(49, OTRO_TEXTO, "No Responde"), NARANJA, id="49-con-motivo"),
        pytest.param(_estado(8, "Entregado", "Rechazado"), CERRADO, id="8-con-motivo"),
    ],
)
def test_precedencia_entre_reglas(estado: EstadoOca, esperado: ClasificacionEnvio) -> None:
    assert clasificar_estado(estado, _contexto(LUNES_21_SEP)) == esperado


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
    estado = _estado(id_estado, OTRO_TEXTO, "Sin Motivo")

    assert clasificar_estado(estado, _contexto(LUNES_21_SEP)) == esperado


@pytest.mark.parametrize("id_estado", VERDES_DEL_CATALOGO)
def test_todo_verde_con_motivo_pasa_a_naranja(id_estado: int) -> None:
    estado = _estado(id_estado, OTRO_TEXTO, "No Responde")

    assert clasificar_estado(estado, _contexto(LUNES_21_SEP)) == NARANJA


def test_estado_nuevo_con_motivo_es_naranja_y_se_marca_desconocido() -> None:
    estado = _estado(99, "texto nuevo", "No Responde")

    clasificacion = clasificar_estado(estado, _contexto(LUNES_21_SEP))

    assert clasificacion == replace(
        NARANJA, observacion="Estado nuevo, revisar", estado_desconocido=True
    )


def test_texto_sin_id_estado_que_no_es_acuse_es_estado_nuevo() -> None:
    estado = _estado(None, "Otro estado sin id", "Sin Motivo")

    assert clasificar_estado(estado, _contexto(LUNES_21_SEP)) == ESTADO_NUEVO


def test_estado_nuevo_no_espera_dias_sin_movimiento() -> None:
    estado = _estado(99, "texto nuevo", "Sin Motivo")

    assert clasificar_estado(estado, _contexto(date(2026, 10, 30))) == ESTADO_NUEVO


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
    estado = _estado(None, texto, "Sin Motivo")

    assert clasificar_estado(estado, _contexto(LUNES_21_SEP)) == CERRADO


@pytest.mark.parametrize("motivo", ["", "   ", "sin motivo", "  SIN   Motivo ", "Sin Motívo"])
def test_sin_motivo_normalizado_o_vacio_no_es_motivo(motivo: str) -> None:
    estado = _estado(35, "Programado para visita a domicilio", motivo)

    assert clasificar_estado(estado, _contexto(LUNES_21_SEP)) == VERDE


def test_normalizar_texto() -> None:
    assert normalizar_texto("  Envío   a Rendir\ta OTRA Suc ") == "envio a rendir a otra suc"


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
    estado = _con_fecha(_estado(10, EN_VIAJE, "Sin Motivo"), fecha_estado)

    assert clasificar_estado(estado, _contexto(hoy)) == esperado


def test_sin_movimiento_en_singular() -> None:
    contexto = ContextoClasificacion(
        hoy=date(2026, 9, 22), feriados=frozenset(), dias_sin_movimiento=1
    )

    clasificacion = clasificar_estado(_estado(1, OTRO_TEXTO, "Sin Motivo"), contexto)

    assert clasificacion == replace(AMARILLO, observacion="Sin movimiento hace 1 día hábil")


def test_sin_movimiento_no_cuenta_feriados() -> None:
    estado = _con_fecha(_estado(10, EN_VIAJE, "Sin Motivo"), VIERNES_9_OCT)

    clasificacion = clasificar_estado(estado, _contexto(date(2026, 10, 14), FERIADO_12_OCT))

    assert clasificacion == VERDE  # 13 y 14 de octubre: 2 días hábiles


@pytest.mark.parametrize(
    ("estado", "esperado"),
    [
        pytest.param(_estado(45, EN_ESPERA, "Sin Motivo"), ROJO_LIMITE_25_SEP, id="45-rojo"),
        pytest.param(
            _estado(48, "Reprogramado para nueva visita", "No Responde"), NARANJA, id="48-naranja"
        ),
        pytest.param(_estado(10, EN_VIAJE, "No Responde"), NARANJA, id="10-con-motivo"),
        pytest.param(_estado(49, OTRO_TEXTO, "Sin Motivo"), GRIS_ABIERTO, id="49-gris-abierto"),
    ],
)
def test_sin_movimiento_solo_pasa_a_amarillo_a_los_verdes(
    estado: EstadoOca, esperado: ClasificacionEnvio
) -> None:
    """Rojo, naranja y gris abierto no cambian de color aunque `FechaEstado` no se mueva."""
    assert clasificar_estado(estado, _contexto(VIERNES_30_OCT)) == esperado


@pytest.mark.parametrize(
    "hoy",
    [
        pytest.param(date(2026, 9, 24), id="3-dias-habiles-despues"),
        pytest.param(date(2026, 9, 25), id="el-dia-limite"),
        pytest.param(date(2026, 9, 30), id="limite-vencido"),
    ],
)
def test_limite_de_retiro_se_cuenta_desde_fecha_estado(hoy: date) -> None:
    """El job corre varias veces por día: el límite no se corre con `hoy` ni pasa a amarillo."""
    estado = _estado(45, EN_ESPERA, "Sin Motivo")

    assert clasificar_estado(estado, _contexto(hoy)) == ROJO_LIMITE_25_SEP


def test_limite_de_retiro_cruza_feriado_aunque_hoy_sea_posterior() -> None:
    estado = _con_fecha(_estado(45, EN_ESPERA, "Sin Motivo"), VIERNES_9_OCT)

    clasificacion = clasificar_estado(estado, _contexto(date(2026, 10, 14), FERIADO_12_OCT))

    assert clasificacion.fecha_limite == date(2026, 10, 16)


def test_rojo_con_ingreso_en_fin_de_semana() -> None:
    """Ingresó el sábado 26/09: el día 1 es el lunes 28/09 y el límite el viernes 02/10."""
    estado = _con_fecha(_estado(45, EN_ESPERA, "Sin Motivo"), date(2026, 9, 26))

    clasificacion = clasificar_estado(estado, _contexto(date(2026, 9, 26)))

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
    assert clasificar_sin_datos(LUNES_21_SEP, _contexto(hoy)) == esperado


def test_texto_de_acuse_con_id_estado_no_cierra_el_envio() -> None:
    """El acuse se reconoce por texto solo cuando OCA no manda `IdEstado`: con un id
    desconocido, manda el id y el envío queda para revisar."""
    estado = _estado(99, "Acuse en Rendicion", "Sin Motivo")

    assert clasificar_estado(estado, _contexto(LUNES_21_SEP)) == ESTADO_NUEVO
