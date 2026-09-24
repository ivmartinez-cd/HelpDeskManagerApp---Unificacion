"""Tests del seguimiento de un envío: alta desde Siges, aplicación de la respuesta de OCA y
registro de un error de consulta.

`HOY` es el jueves 24/09/2026 (sin feriados en la semana): un remito o `FechaEstado` del
lunes 21/09 lleva 3 días hábiles, uno del viernes 18/09 lleva 4.
"""

from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any

import pytest

from src.modules.insumos.domain.entities.despachados.envio_seguido import (
    CierreAlerta,
    EnvioSeguido,
    ErrorConsulta,
)
from src.modules.insumos.domain.services.despachados.seguimiento import (
    MomentoConsulta,
    aplicar_consulta,
    nuevo_envio,
    registrar_error,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import (
    ClasificacionEnvio,
    ColorSemaforo,
    ContextoClasificacion,
)
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import DespachoSiges
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca

GUIA = "3867500000000000001"
HOY = date(2026, 9, 24)
LUNES_21_SEP = date(2026, 9, 21)
VIERNES_18_SEP = date(2026, 9, 18)
AHORA = datetime(2026, 9, 24, 15, 0, tzinfo=UTC)
ANTES = datetime(2026, 9, 24, 13, 0, tzinfo=UTC)
CONTEXTO = ContextoClasificacion(hoy=HOY, feriados=frozenset())
MOMENTO = MomentoConsulta(ahora=AHORA, contexto=CONTEXTO)
CIERRE = CierreAlerta(cerrada_en=ANTES, usuario_id=None, usuario_nombre="Ana Operadora")

VERDE = ClasificacionEnvio(
    color=ColorSemaforo.VERDE,
    alerta=False,
    abierto=True,
    fecha_limite=None,
    observacion="",
    estado_desconocido=False,
)
NARANJA = replace(VERDE, color=ColorSemaforo.NARANJA, alerta=True)
ROJO_LIMITE_25_SEP = replace(
    VERDE, color=ColorSemaforo.ROJO, alerta=True, fecha_limite=date(2026, 9, 25)
)
SIN_DATOS = replace(VERDE, color=ColorSemaforo.AMARILLO, observacion="Sin datos en OCA")
ESPERANDO_INGRESO = replace(VERDE, observacion="Esperando ingreso en OCA")


def _despacho(id_remito: int, fecha_remito: date, **cambios: Any) -> DespachoSiges:
    base = DespachoSiges(
        id_remito=id_remito,
        numero_remito=50000 + id_remito,
        guia=GUIA,
        id_distribucion=3,
        fecha_remito=fecha_remito,
        bultos=1,
        cliente=f"Cliente del remito {id_remito}",
        sucursal_cliente=f"Sucursal {id_remito}",
        entrega_a="",
        incidentes=(),
    )
    return replace(base, **cambios)


def _estado(**cambios: Any) -> EstadoOca:
    """En viaje (verde) con `FechaEstado` el lunes 21/09/2026."""
    base = EstadoOca(
        numero_envio=GUIA,
        operativa="434324",
        orden_retiro="",
        sucursal_actual="Rosario",
        fecha_estado=LUNES_21_SEP,
        estado="En viaje a Centro de Distribución de Destino",
        id_estado=10,
        motivo="Sin Motivo",
        cantidad_paquetes=1,
    )
    return replace(base, **cambios)


def _envio(**cambios: Any) -> EnvioSeguido:
    base = EnvioSeguido(
        guia=GUIA,
        id_distribucion=3,
        fecha_remito=LUNES_21_SEP,
        cliente="Cliente Test",
        sucursal_cliente="Casa Central",
        clasificacion=VERDE,
    )
    return replace(base, **cambios)


class TestNuevoEnvio:
    def test_toma_los_datos_de_siges_del_remito_mas_viejo(self) -> None:
        despachos = [
            _despacho(7, date(2026, 9, 23)),
            _despacho(5, LUNES_21_SEP, id_distribucion=9),
            _despacho(3, date(2026, 9, 23)),
        ]

        envio = nuevo_envio(despachos, CONTEXTO)

        assert envio == EnvioSeguido(
            guia=GUIA,
            id_distribucion=9,
            fecha_remito=LUNES_21_SEP,
            cliente="Cliente del remito 5",
            sucursal_cliente="Sucursal 5",
            clasificacion=SIN_DATOS,
        )

    def test_con_la_misma_fecha_desempata_el_id_de_remito(self) -> None:
        despachos = [_despacho(9, LUNES_21_SEP), _despacho(4, LUNES_21_SEP)]

        assert nuevo_envio(despachos, CONTEXTO).cliente == "Cliente del remito 4"

    def test_un_remito_reciente_espera_el_ingreso_en_oca(self) -> None:
        envio = nuevo_envio([_despacho(1, date(2026, 9, 23))], CONTEXTO)

        assert envio.clasificacion == ESPERANDO_INGRESO
        assert envio.estado_oca is None

    def test_sin_remitos_es_un_error(self) -> None:
        with pytest.raises(ValueError, match="al menos un remito"):
            nuevo_envio([], CONTEXTO)

    def test_remitos_de_guias_distintas_es_un_error(self) -> None:
        otra = _despacho(2, LUNES_21_SEP, guia="3867500000000000002")

        with pytest.raises(ValueError, match="guías distintas"):
            nuevo_envio([_despacho(1, LUNES_21_SEP), otra], CONTEXTO)


class TestAplicarConsulta:
    def test_el_primer_estado_es_un_cambio(self) -> None:
        error_viejo = ErrorConsulta(mensaje="timeout", ocurrido_en=ANTES)
        en_viaje = _estado(fecha_estado=date(2026, 9, 23))

        resultado = aplicar_consulta(_envio(ultimo_error=error_viejo), en_viaje, MOMENTO)

        assert resultado.cambio_estado is True
        assert resultado.envio == _envio(
            estado_oca=en_viaje, clasificacion=VERDE, consultado_en=AHORA, ultimo_error=None
        )

    @pytest.mark.parametrize(
        "cambios",
        [
            pytest.param(
                {"estado": "  EN VIAJE a centro de distribucion   de destino "}, id="estado"
            ),
            pytest.param({"motivo": ""}, id="motivo-vacio-es-sin-motivo"),
            pytest.param({"motivo": " sin  MOTIVO "}, id="motivo"),
            pytest.param({"sucursal_actual": " rosario"}, id="sucursal"),
            pytest.param({"operativa": "434305", "cantidad_paquetes": 2}, id="fuera-de-la-clave"),
        ],
    )
    def test_mismo_estado_con_otro_formato_no_es_un_cambio(self, cambios: dict[str, Any]) -> None:
        nuevo = _estado(**cambios)

        resultado = aplicar_consulta(_envio(estado_oca=_estado()), nuevo, MOMENTO)

        assert resultado.cambio_estado is False
        assert resultado.envio.estado_oca == nuevo
        assert resultado.envio.consultado_en == AHORA

    @pytest.mark.parametrize(
        "cambios",
        [
            pytest.param({"id_estado": 34}, id="id-estado"),
            pytest.param({"estado": "En distribución"}, id="estado"),
            pytest.param({"motivo": "Domicilio Incompleto"}, id="motivo"),
            pytest.param({"sucursal_actual": "Córdoba"}, id="sucursal"),
            pytest.param({"fecha_estado": date(2026, 9, 22)}, id="fecha-estado"),
        ],
    )
    def test_cambia_si_cambia_un_campo_de_la_clave(self, cambios: dict[str, Any]) -> None:
        resultado = aplicar_consulta(_envio(estado_oca=_estado()), _estado(**cambios), MOMENTO)

        assert resultado.cambio_estado is True

    def test_sin_datos_y_sin_estado_previo_clasifica_por_el_remito(self) -> None:
        resultado = aplicar_consulta(_envio(), None, MOMENTO)

        assert resultado.cambio_estado is False
        assert resultado.envio == _envio(clasificacion=SIN_DATOS, consultado_en=AHORA)

    def test_sin_datos_conserva_el_ultimo_estado_y_reclasifica(self) -> None:
        anterior = _estado(fecha_estado=VIERNES_18_SEP)
        envio = _envio(estado_oca=anterior, cierre_alerta=CIERRE)

        resultado = aplicar_consulta(envio, None, MOMENTO)

        assert resultado.cambio_estado is False
        assert resultado.envio.estado_oca == anterior
        assert resultado.envio.cierre_alerta == CIERRE
        assert resultado.envio.clasificacion == replace(
            VERDE, color=ColorSemaforo.AMARILLO, observacion="Sin movimiento hace 4 días hábiles"
        )

    def test_un_cambio_a_un_estado_con_alerta_reabre_la_alerta(self) -> None:
        visita_fallida = _estado(id_estado=48, estado="Reprogramado", motivo="No Responde")
        envio = _envio(estado_oca=visita_fallida, clasificacion=NARANJA, cierre_alerta=CIERRE)

        resultado = aplicar_consulta(envio, _estado(id_estado=45, estado="En Espera"), MOMENTO)

        assert resultado.cambio_estado is True
        assert resultado.envio.clasificacion == ROJO_LIMITE_25_SEP
        assert resultado.envio.cierre_alerta is None
        assert resultado.envio.alerta_abierta is True

    def test_un_cambio_a_un_estado_sin_alerta_conserva_el_cierre(self) -> None:
        envio = _envio(
            estado_oca=_estado(id_estado=48), clasificacion=NARANJA, cierre_alerta=CIERRE
        )

        resultado = aplicar_consulta(envio, _estado(id_estado=8, estado="Entregado"), MOMENTO)

        assert resultado.cambio_estado is True
        assert resultado.envio.cierre_alerta == CIERRE

    def test_sin_cambio_la_alerta_cerrada_sigue_cerrada(self) -> None:
        en_espera = _estado(id_estado=45, estado="En Espera")
        envio = _envio(estado_oca=en_espera, clasificacion=VERDE, cierre_alerta=CIERRE)

        resultado = aplicar_consulta(envio, en_espera, MOMENTO)

        assert resultado.envio.clasificacion == ROJO_LIMITE_25_SEP
        assert resultado.envio.cierre_alerta == CIERRE
        assert resultado.envio.alerta_abierta is False


class TestRegistrarError:
    def test_guarda_el_error_y_reclasifica_con_el_ultimo_estado(self) -> None:
        en_espera = _estado(id_estado=45, estado="En Espera")
        envio = _envio(estado_oca=en_espera, consultado_en=ANTES, cierre_alerta=CIERRE)

        con_error = registrar_error(envio, "OCA no respondió", MOMENTO)

        assert con_error == replace(
            envio,
            clasificacion=ROJO_LIMITE_25_SEP,
            ultimo_error=ErrorConsulta(mensaje="OCA no respondió", ocurrido_en=AHORA),
        )

    def test_sin_estado_previo_reclasifica_por_el_remito(self) -> None:
        con_error = registrar_error(_envio(), "timeout", MOMENTO)

        assert con_error.clasificacion == SIN_DATOS
        assert con_error.estado_oca is None
        assert con_error.consultado_en is None
