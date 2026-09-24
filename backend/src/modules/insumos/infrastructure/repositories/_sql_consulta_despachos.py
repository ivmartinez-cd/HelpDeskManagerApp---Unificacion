"""SQL de la pantalla de Despachados: alcance, filtros, orden por urgencia y columnas de cada
fila (primer remito, incidentes y última acción) resueltas en la misma consulta, sin N+1.

Todo parametrizado: el texto del usuario va como parámetro de ILIKE, con `%`, `_` y `\\`
escapados para que se busquen literales.
"""

from datetime import date
from typing import Any

from sqlalchemy import (
    ColumnElement,
    Select,
    String,
    and_,
    case,
    cast,
    func,
    or_,
    select,
    true,
)
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.selectable import LateralFromClause

from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    FiltrosDespachos,
    Pagina,
)
from src.modules.insumos.infrastructure.models.despacho_accion_model import DespachoAccionModel
from src.modules.insumos.infrastructure.models.despacho_envio_model import DespachoEnvioModel
from src.modules.insumos.infrastructure.models.despacho_remito_model import (
    DespachoIncidenteModel,
    DespachoRemitoModel,
)

_ENVIO = DespachoEnvioModel
_REMITO = DespachoRemitoModel
_INCIDENTE = DespachoIncidenteModel
_ACCION = DespachoAccionModel
_ESCAPE = "\\"
_ColumnaTexto = ColumnElement[str] | InstrumentedAttribute[str]

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


def alerta_abierta() -> ColumnElement[bool]:
    return and_(_ENVIO.alerta, _ENVIO.alerta_cerrada_en.is_(None))


def en_alcance(alcance_desde: date) -> ColumnElement[bool]:
    """Abiertos siempre; cerrados solo con remito desde `alcance_desde`."""
    return or_(_ENVIO.abierto, _ENVIO.fecha_remito >= alcance_desde)


def condiciones(filtros: FiltrosDespachos) -> list[ColumnElement[bool]]:
    """Alcance y filtros de la pantalla; un filtro vacío (o `None`) no filtra."""
    resultado = [en_alcance(filtros.alcance_desde)]
    if filtros.colores:
        resultado.append(_ENVIO.color.in_([c.value for c in filtros.colores]))
    if filtros.operativa:
        resultado.append(_ENVIO.oca_operativa == filtros.operativa)
    if filtros.remito_desde is not None:
        resultado.append(_ENVIO.fecha_remito >= filtros.remito_desde)
    if filtros.remito_hasta is not None:
        resultado.append(_ENVIO.fecha_remito <= filtros.remito_hasta)
    if filtros.solo_alertas_abiertas:
        resultado.append(alerta_abierta())
    if filtros.texto.strip():
        resultado.append(_coincide_texto(filtros.texto.strip()))
    return resultado


def _patron_literal(texto: str) -> str:
    """`%texto%` con los comodines de LIKE del usuario escapados (se buscan literales)."""
    escapado = texto.replace(_ESCAPE, _ESCAPE * 2).replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


def _coincide_texto(texto: str) -> ColumnElement[bool]:
    patron = _patron_literal(texto)

    def coincide(columna: _ColumnaTexto) -> ColumnElement[bool]:
        return columna.ilike(patron, escape=_ESCAPE)

    del_remito = _REMITO.guia == _ENVIO.guia
    remito = select(_REMITO.id_remito).where(
        del_remito, coincide(cast(_REMITO.numero_remito, String))
    )
    incidente = (
        select(_INCIDENTE.id_remito)
        .join(_REMITO, _REMITO.id_remito == _INCIDENTE.id_remito)
        .where(del_remito, or_(coincide(_INCIDENTE.numero), coincide(_INCIDENTE.numero_cliente)))
    )
    return or_(coincide(_ENVIO.guia), coincide(_ENVIO.cliente), remito.exists(), incidente.exists())


def _orden_por_urgencia() -> tuple[ColumnElement[Any], ...]:
    """Rojo, naranja, amarillo, verde, gris, cerrado. Rojo por fecha límite; naranja y
    amarillo por fecha de estado más vieja; el resto por la más nueva. Desempata la guía."""
    rango = case(_RANGO_URGENCIA, value=_ENVIO.color, else_=len(_RANGO_URGENCIA))
    limite_rojo = case((_ENVIO.color == ColorSemaforo.ROJO.value, _ENVIO.fecha_limite))
    estado_en_espera = case((_ENVIO.color.in_(_EN_ESPERA), _ENVIO.oca_fecha_estado))
    estado_resto = case((_ENVIO.color.in_(_RESTO), _ENVIO.oca_fecha_estado))
    return (
        rango,
        limite_rojo.asc().nulls_last(),
        estado_en_espera.asc().nulls_last(),
        estado_resto.desc().nulls_last(),
        _ENVIO.guia.asc(),
    )


def _primer_remito() -> LateralFromClause:
    """LATERAL con el primer remito de la guía (por fecha e id) y su primer incidente."""
    primer_incidente = (
        select(_INCIDENTE.numero)
        .where(_INCIDENTE.id_remito == _REMITO.id_remito)
        .order_by(_INCIDENTE.numero)
        .limit(1)
        .correlate(_REMITO)
        .scalar_subquery()
    )
    return (
        select(_REMITO.numero_remito, primer_incidente.label("incidente"))
        .where(_REMITO.guia == _ENVIO.guia)
        .order_by(_REMITO.fecha_remito, _REMITO.id_remito)
        .limit(1)
        .lateral("primer_remito")
    )


def _ultima_accion() -> LateralFromClause:
    return (
        select(_ACCION.tipo, _ACCION.resultado, _ACCION.usuario_nombre, _ACCION.creada_en)
        .where(_ACCION.guia == _ENVIO.guia)
        .order_by(_ACCION.creada_en.desc(), _ACCION.id.desc())
        .limit(1)
        .lateral("ultima_accion")
    )


def _cantidad_remitos() -> ColumnElement[int]:
    return (
        select(func.count())
        .select_from(_REMITO)
        .where(_REMITO.guia == _ENVIO.guia)
        .correlate(_ENVIO)
        .scalar_subquery()
    )


def _cantidad_incidentes() -> ColumnElement[int]:
    """Incidentes distintos (por número) entre todos los remitos de la guía."""
    return (
        select(func.count(func.distinct(_INCIDENTE.numero)))
        .select_from(_INCIDENTE)
        .join(_REMITO, _REMITO.id_remito == _INCIDENTE.id_remito)
        .where(_REMITO.guia == _ENVIO.guia)
        .correlate(_ENVIO)
        .scalar_subquery()
    )


_PRIMER_REMITO = _primer_remito()
_ULTIMA_ACCION = _ultima_accion()

# Etiquetas = nombres de campo de `FilaDespacho` (salvo `accion_*`, que arman `UltimaAccion`).
_COLUMNAS_FILA = (
    _ENVIO.guia.label("guia"),
    _ENVIO.color.label("color"),
    alerta_abierta().label("alerta_abierta"),
    _ENVIO.observacion.label("observacion"),
    _ENVIO.fecha_limite.label("fecha_limite"),
    func.coalesce(_ENVIO.oca_estado, "").label("estado"),
    func.coalesce(_ENVIO.oca_motivo, "").label("motivo"),
    func.coalesce(_ENVIO.oca_sucursal, "").label("sucursal_oca"),
    _ENVIO.oca_fecha_estado.label("fecha_estado"),
    func.coalesce(_ENVIO.oca_operativa, "").label("operativa"),
    _ENVIO.cliente.label("cliente"),
    _ENVIO.fecha_remito.label("fecha_remito"),
    _PRIMER_REMITO.c.numero_remito.label("numero_remito"),
    _cantidad_remitos().label("cantidad_remitos"),
    func.coalesce(_PRIMER_REMITO.c.incidente, "").label("incidente"),
    _cantidad_incidentes().label("cantidad_incidentes"),
    _ENVIO.ultimo_error_en.is_not(None).label("con_error"),
    _ULTIMA_ACCION.c.tipo.label("accion_tipo"),
    _ULTIMA_ACCION.c.resultado.label("accion_resultado"),
    _ULTIMA_ACCION.c.usuario_nombre.label("accion_usuario_nombre"),
    _ULTIMA_ACCION.c.creada_en.label("accion_creada_en"),
)


def listar_filas(filtros: FiltrosDespachos, pagina: Pagina) -> Select[Any]:
    """Una página de filas, ordenada por urgencia, en una sola sentencia."""
    return (
        select(*_COLUMNAS_FILA)
        .select_from(_ENVIO)
        .outerjoin(_PRIMER_REMITO, true())
        .outerjoin(_ULTIMA_ACCION, true())
        .where(*condiciones(filtros))
        .order_by(*_orden_por_urgencia())
        .limit(pagina.limite)
        .offset(pagina.desplazamiento)
    )


def contar_filas(filtros: FiltrosDespachos) -> Select[Any]:
    return select(func.count()).select_from(_ENVIO).where(*condiciones(filtros))


def resumen_por_color(alcance_desde: date) -> Select[Any]:
    """Por color: cantidad, alertas abiertas, naranjas sin acción y fecha límite mínima."""
    sin_accion = and_(
        _ENVIO.color == ColorSemaforo.NARANJA.value,
        ~select(_ACCION.id).where(_ACCION.guia == _ENVIO.guia).exists(),
    )
    return (
        select(
            _ENVIO.color.label("color"),
            func.count().label("cantidad"),
            func.count().filter(alerta_abierta()).label("alertas_abiertas"),
            func.count().filter(sin_accion).label("sin_accion"),
            func.min(_ENVIO.fecha_limite).label("limite_min"),
        )
        .where(en_alcance(alcance_desde))
        .group_by(_ENVIO.color)
    )


def operativas_presentes(alcance_desde: date) -> Select[Any]:
    return (
        select(_ENVIO.oca_operativa)
        .distinct()
        .where(en_alcance(alcance_desde), _ENVIO.oca_operativa != "")
        .order_by(_ENVIO.oca_operativa)
    )
