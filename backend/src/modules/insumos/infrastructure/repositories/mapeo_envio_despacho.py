"""Mapeo entre la tabla `insumos_despacho_envio` y la entidad `EnvioSeguido`.

Las columnas `oca_*` son NULL mientras OCA no registre la guía: el estado se reconstruye
solo si hay `oca_fecha_estado`. El error de consulta y el cierre de la alerta se
reconstruyen solo si tienen fecha (`ultimo_error_en`, `alerta_cerrada_en`).
"""

from typing import Any

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

_COLUMNAS_OCA = (
    "oca_id_estado",
    "oca_estado",
    "oca_motivo",
    "oca_sucursal",
    "oca_fecha_estado",
    "oca_operativa",
    "oca_orden_retiro",
    "oca_cantidad_paquetes",
)


def envio_desde_fila(fila: DespachoEnvioModel) -> EnvioSeguido:
    return EnvioSeguido(
        guia=fila.guia,
        id_distribucion=fila.id_distribucion,
        fecha_remito=fila.fecha_remito,
        cliente=fila.cliente,
        sucursal_cliente=fila.sucursal_cliente,
        clasificacion=_clasificacion(fila),
        estado_oca=_estado_oca(fila),
        consultado_en=fila.consultado_en,
        ultimo_error=_error_consulta(fila),
        cierre_alerta=_cierre_alerta(fila),
    )


def columnas_alta(envio: EnvioSeguido) -> dict[str, Any]:
    """Todas las columnas de un envío nuevo (las fechas de auditoría las pone la base)."""
    return {
        "guia": envio.guia,
        "id_distribucion": envio.id_distribucion,
        "fecha_remito": envio.fecha_remito,
        "cliente": envio.cliente,
        "sucursal_cliente": envio.sucursal_cliente,
        **columnas_seguimiento(envio),
    }


def columnas_seguimiento(envio: EnvioSeguido) -> dict[str, Any]:
    """Lo que cambia con cada consulta a OCA o cierre de alerta: todo menos los datos de
    Siges (guía, distribución, fecha de remito, cliente y sucursal)."""
    return {
        **_columnas_oca(envio.estado_oca),
        **_columnas_clasificacion(envio.clasificacion),
        "consultado_en": envio.consultado_en,
        **_columnas_error(envio.ultimo_error),
        **_columnas_cierre(envio.cierre_alerta),
    }


def _estado_oca(fila: DespachoEnvioModel) -> EstadoOca | None:
    if fila.oca_fecha_estado is None:
        return None
    return EstadoOca(
        numero_envio=fila.guia,
        operativa=fila.oca_operativa or "",
        orden_retiro=fila.oca_orden_retiro or "",
        sucursal_actual=fila.oca_sucursal or "",
        fecha_estado=fila.oca_fecha_estado,
        estado=fila.oca_estado or "",
        id_estado=fila.oca_id_estado,
        motivo=fila.oca_motivo or "",
        cantidad_paquetes=fila.oca_cantidad_paquetes,
    )


def _clasificacion(fila: DespachoEnvioModel) -> ClasificacionEnvio:
    return ClasificacionEnvio(
        color=ColorSemaforo(fila.color),
        alerta=fila.alerta,
        abierto=fila.abierto,
        fecha_limite=fila.fecha_limite,
        observacion=fila.observacion,
        estado_desconocido=fila.estado_desconocido,
    )


def _error_consulta(fila: DespachoEnvioModel) -> ErrorConsulta | None:
    if fila.ultimo_error_en is None:
        return None
    return ErrorConsulta(mensaje=fila.ultimo_error or "", ocurrido_en=fila.ultimo_error_en)


def _cierre_alerta(fila: DespachoEnvioModel) -> CierreAlerta | None:
    if fila.alerta_cerrada_en is None:
        return None
    return CierreAlerta(
        cerrada_en=fila.alerta_cerrada_en,
        usuario_id=fila.alerta_cerrada_por_id,
        usuario_nombre=fila.alerta_cerrada_por_nombre or "",
    )


def _columnas_oca(estado: EstadoOca | None) -> dict[str, Any]:
    if estado is None:
        return dict.fromkeys(_COLUMNAS_OCA)
    return {
        "oca_id_estado": estado.id_estado,
        "oca_estado": estado.estado,
        "oca_motivo": estado.motivo,
        "oca_sucursal": estado.sucursal_actual,
        "oca_fecha_estado": estado.fecha_estado,
        "oca_operativa": estado.operativa,
        "oca_orden_retiro": estado.orden_retiro,
        "oca_cantidad_paquetes": estado.cantidad_paquetes,
    }


def _columnas_clasificacion(clasificacion: ClasificacionEnvio) -> dict[str, Any]:
    return {
        "color": clasificacion.color.value,
        "alerta": clasificacion.alerta,
        "abierto": clasificacion.abierto,
        "fecha_limite": clasificacion.fecha_limite,
        "observacion": clasificacion.observacion,
        "estado_desconocido": clasificacion.estado_desconocido,
    }


def _columnas_error(error: ErrorConsulta | None) -> dict[str, Any]:
    if error is None:
        return {"ultimo_error": None, "ultimo_error_en": None}
    return {"ultimo_error": error.mensaje, "ultimo_error_en": error.ocurrido_en}


def _columnas_cierre(cierre: CierreAlerta | None) -> dict[str, Any]:
    if cierre is None:
        return dict.fromkeys(
            ("alerta_cerrada_en", "alerta_cerrada_por_id", "alerta_cerrada_por_nombre")
        )
    return {
        "alerta_cerrada_en": cierre.cerrada_en,
        "alerta_cerrada_por_id": cierre.usuario_id,
        "alerta_cerrada_por_nombre": cierre.usuario_nombre,
    }
