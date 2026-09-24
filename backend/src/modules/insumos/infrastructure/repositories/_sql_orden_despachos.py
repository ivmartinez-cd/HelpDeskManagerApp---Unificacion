"""ORDER BY de la tabla de Despachados: por urgencia (el defecto) o por la columna que elija el
operador. Cada columna es una expresión SQLAlchemy fija (nada del usuario llega al SQL salvo
la elección entre valores del enum). Los vacíos van al final en las dos direcciones y
desempata la guía."""

from collections.abc import Callable
from typing import Any

from sqlalchemy import ColumnElement, case, func
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.selectable import LateralFromClause

from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    ColumnaOrden,
    OrdenDespachos,
)
from src.modules.insumos.infrastructure.models.despacho_envio_model import DespachoEnvioModel

_ENVIO = DespachoEnvioModel
_RANGO_URGENCIA = {
    ColorSemaforo.ROJO.value: 0,
    ColorSemaforo.NARANJA.value: 1,
    ColorSemaforo.AMARILLO.value: 2,
    ColorSemaforo.VERDE.value: 3,
    ColorSemaforo.GRIS.value: 4,
    ColorSemaforo.CERRADO.value: 5,
}
_EN_ESPERA = (ColorSemaforo.NARANJA.value, ColorSemaforo.AMARILLO.value)
_RESTO = (ColorSemaforo.VERDE.value, ColorSemaforo.GRIS.value, ColorSemaforo.CERRADO.value)

_Expresion = Callable[[LateralFromClause], ColumnElement[Any] | InstrumentedAttribute[Any]]


def _rango_color() -> ColumnElement[int]:
    return case(_RANGO_URGENCIA, value=_ENVIO.color, else_=len(_RANGO_URGENCIA))


def _texto(columna: Any) -> ColumnElement[Any]:
    """En minúsculas y con "" como vacío (OCA sin datos), para que vaya al final."""
    return func.lower(func.nullif(columna, ""))


_POR_COLUMNA: dict[ColumnaOrden, _Expresion] = {
    ColumnaOrden.COLOR: lambda _: _rango_color(),
    ColumnaOrden.GUIA: lambda _: _ENVIO.guia,
    ColumnaOrden.REMITO: lambda primer_remito: primer_remito.c.numero_remito,
    ColumnaOrden.CLIENTE: lambda _: _texto(_ENVIO.cliente),
    ColumnaOrden.INCIDENTE: lambda primer_remito: _texto(primer_remito.c.incidente),
    ColumnaOrden.ESTADO: lambda _: _texto(_ENVIO.oca_estado),
    ColumnaOrden.SUCURSAL: lambda _: _texto(_ENVIO.oca_sucursal),
    ColumnaOrden.FECHA_REMITO: lambda _: _ENVIO.fecha_remito,
    ColumnaOrden.FECHA_ESTADO: lambda _: _ENVIO.oca_fecha_estado,
    ColumnaOrden.LIMITE: lambda _: _ENVIO.fecha_limite,
}


def orden_filas(
    orden: OrdenDespachos, primer_remito: LateralFromClause
) -> tuple[ColumnElement[Any], ...]:
    """Cláusulas de ORDER BY. `primer_remito` es el LATERAL del listado (remito e incidente)."""
    if orden.columna is ColumnaOrden.URGENCIA:
        return _orden_por_urgencia()
    expresion = _POR_COLUMNA[orden.columna](primer_remito)
    principal = expresion.desc() if orden.descendente else expresion.asc()
    return (principal.nulls_last(), _ENVIO.guia.asc())


def _orden_por_urgencia() -> tuple[ColumnElement[Any], ...]:
    """Rojo, naranja, amarillo, verde, gris, cerrado. Rojo por fecha límite; naranja y
    amarillo por fecha de estado más vieja; el resto por la más nueva. Desempata la guía."""
    limite_rojo = case((_ENVIO.color == ColorSemaforo.ROJO.value, _ENVIO.fecha_limite))
    estado_en_espera = case((_ENVIO.color.in_(_EN_ESPERA), _ENVIO.oca_fecha_estado))
    estado_resto = case((_ENVIO.color.in_(_RESTO), _ENVIO.oca_fecha_estado))
    return (
        _rango_color(),
        limite_rojo.asc().nulls_last(),
        estado_en_espera.asc().nulls_last(),
        estado_resto.desc().nulls_last(),
        _ENVIO.guia.asc(),
    )
