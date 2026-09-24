"""Mapeo entre `insumos_despacho_envio` y `EnvioSeguido`: qué se reconstruye según las
columnas NULL y qué columnas escribe cada operación, sin base de datos."""

import uuid
from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any

import pytest

from src.modules.insumos.domain.entities.despachados.envio_seguido import (
    CierreAlerta,
    EnvioSeguido,
    ErrorConsulta,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import (
    ClasificacionEnvio,
    ColorSemaforo,
)
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca
from src.modules.insumos.infrastructure.models.despacho_envio_model import DespachoEnvioModel
from src.modules.insumos.infrastructure.repositories.mapeo_envio_despacho import (
    columnas_alta,
    columnas_seguimiento,
    envio_desde_fila,
)

_GUIA = "3867500000001234567"
_EN = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
_DATOS_SIGES = {"guia", "id_distribucion", "fecha_remito", "cliente", "sucursal_cliente"}


_ENVIO = EnvioSeguido(
    guia=_GUIA,
    id_distribucion=3,
    fecha_remito=date(2026, 9, 15),
    cliente="Cliente SA",
    sucursal_cliente="Casa Central",
    clasificacion=ClasificacionEnvio(
        ColorSemaforo.NARANJA, True, True, None, "Visita fallida", False
    ),
)
_ESTADO = EstadoOca(
    numero_envio=_GUIA,
    operativa="434324",
    orden_retiro="98765",
    sucursal_actual="Rosario",
    fecha_estado=date(2026, 9, 18),
    estado="Visita",
    id_estado=12,
    motivo="Domicilio cerrado",
    cantidad_paquetes=2,
)


def _envio(**cambios: Any) -> EnvioSeguido:
    return replace(_ENVIO, **cambios)


def _estado(**cambios: Any) -> EstadoOca:
    return replace(_ESTADO, **cambios)


def _fila(envio: EnvioSeguido, **cambios: Any) -> DespachoEnvioModel:
    return DespachoEnvioModel(**{**columnas_alta(envio), **cambios})


@pytest.mark.parametrize(
    "envio",
    [
        _envio(),
        _envio(estado_oca=_estado(), consultado_en=_EN),
        _envio(estado_oca=_estado(id_estado=None, motivo="", cantidad_paquetes=None)),
        _envio(ultimo_error=ErrorConsulta("Timeout de OCA", _EN)),
        _envio(cierre_alerta=CierreAlerta(_EN, uuid.uuid4(), "Ana Operadora")),
        _envio(cierre_alerta=CierreAlerta(_EN, None, "Usuario dado de baja")),
    ],
)
def test_ida_y_vuelta_por_la_fila(envio: EnvioSeguido) -> None:
    assert envio_desde_fila(_fila(envio)) == envio


def test_sin_fecha_de_estado_no_hay_estado_oca_aunque_haya_otras_columnas() -> None:
    fila = _fila(_envio(), oca_estado="Visita", oca_id_estado=12, oca_fecha_estado=None)

    assert envio_desde_fila(fila).estado_oca is None


def test_textos_oca_null_se_leen_como_vacios() -> None:
    fila = _fila(
        _envio(estado_oca=_estado()),
        oca_operativa=None,
        oca_orden_retiro=None,
        oca_sucursal=None,
        oca_estado=None,
        oca_motivo=None,
    )

    estado = envio_desde_fila(fila).estado_oca

    assert estado == _estado(
        operativa="", orden_retiro="", sucursal_actual="", estado="", motivo=""
    )


def test_error_y_cierre_se_reconstruyen_solo_con_su_fecha() -> None:
    sin_fechas = _fila(_envio(), ultimo_error="Timeout", alerta_cerrada_por_nombre="Ana Operadora")
    con_fechas_y_textos_null = _fila(_envio(), ultimo_error_en=_EN, alerta_cerrada_en=_EN)

    assert envio_desde_fila(sin_fechas).ultimo_error is None
    assert envio_desde_fila(sin_fechas).cierre_alerta is None
    reconstruido = envio_desde_fila(con_fechas_y_textos_null)
    assert reconstruido.ultimo_error == ErrorConsulta("", _EN)
    assert reconstruido.cierre_alerta == CierreAlerta(_EN, None, "")


def test_sin_estado_oca_el_seguimiento_pone_en_null_todas_las_columnas_oca() -> None:
    columnas = columnas_seguimiento(_envio())

    oca = {nombre: valor for nombre, valor in columnas.items() if nombre.startswith("oca_")}
    assert len(oca) == 8
    assert set(oca.values()) == {None}


def test_el_seguimiento_no_incluye_datos_de_siges_y_el_alta_si() -> None:
    envio = _envio(estado_oca=_estado())

    assert _DATOS_SIGES.isdisjoint(columnas_seguimiento(envio))
    assert columnas_alta(envio).keys() == columnas_seguimiento(envio).keys() | _DATOS_SIGES
    assert columnas_seguimiento(envio)["color"] == "naranja"


def test_el_alta_escribe_todas_las_columnas_salvo_las_de_auditoria() -> None:
    columnas_tabla = {c.name for c in DespachoEnvioModel.__table__.columns}

    assert columnas_alta(_envio()).keys() == columnas_tabla - {"creado_en", "actualizado_en"}
