"""Seguimiento de un envío OCA: el alta desde los remitos de Siges y cómo queda después de
cada consulta a OCA (o de su error).

Puro: la hora de la consulta y el calendario llegan de quien llama. Cada consulta vuelve a
clasificar el envío, aunque OCA no informe nada nuevo, porque las reglas que dependen de la
fecha (plazo de retiro, días sin movimiento) cambian con el paso de los días.
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime

from src.modules.insumos.domain.entities.despachados.envio_seguido import (
    EnvioSeguido,
    ErrorConsulta,
)
from src.modules.insumos.domain.services.despachados.semaforo import (
    SIN_MOTIVO,
    clasificar_estado,
    clasificar_sin_datos,
    normalizar_texto,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import (
    ClasificacionEnvio,
    ContextoClasificacion,
)
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import DespachoSiges
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca

_SIN_MOTIVO_NORMALIZADO = normalizar_texto(SIN_MOTIVO)

ClaveEstado = tuple[int | None, str, str, str, date]
"""Lo que distingue un estado de OCA de otro a los fines del historial."""


@dataclass(frozen=True, slots=True)
class MomentoConsulta:
    """Cuándo se consultó OCA y con qué calendario se clasifica el envío."""

    ahora: datetime
    """Instante de la consulta (aware, UTC)."""
    contexto: ContextoClasificacion


@dataclass(frozen=True, slots=True)
class ResultadoConsulta:
    envio: EnvioSeguido
    cambio_estado: bool
    """OCA informó un estado distinto del último conocido (o el primero): va al historial."""


def nuevo_envio(
    despachos: Sequence[DespachoSiges], contexto: ContextoClasificacion
) -> EnvioSeguido:
    """Alta de una guía que Siges despachó y Despachados todavía no sigue. Los datos de
    Siges salen del remito más viejo (por fecha e id); como OCA todavía no informó nada, se
    clasifica por la fecha de ese remito. Todos los despachos tienen que ser de la misma
    guía (`ValueError` si no, o si no llega ninguno)."""
    primero = _remito_mas_viejo(despachos)
    return EnvioSeguido(
        guia=primero.guia,
        id_distribucion=primero.id_distribucion,
        fecha_remito=primero.fecha_remito,
        cliente=primero.cliente,
        sucursal_cliente=primero.sucursal_cliente,
        clasificacion=clasificar_sin_datos(primero.fecha_remito, contexto),
    )


def aplicar_consulta(
    envio: EnvioSeguido, estado: EstadoOca | None, momento: MomentoConsulta
) -> ResultadoConsulta:
    """Cómo queda el envío después de que OCA respondió. Con `estado` None (OCA no tiene
    datos de la guía) se conserva el último estado conocido, si lo había. Si el estado
    cambió y el nuevo requiere acción, la alerta se reabre aunque un operador la hubiera
    cerrado: es otro problema."""
    if estado is None:
        clasificacion = _reclasificar(envio, momento.contexto)
        return ResultadoConsulta(_consultado(envio, clasificacion, momento.ahora), False)
    cambio = envio.estado_oca is None or clave_estado(estado) != clave_estado(envio.estado_oca)
    clasificacion = clasificar_estado(estado, momento.contexto)
    cierre = None if cambio and clasificacion.alerta else envio.cierre_alerta
    actualizado = replace(envio, estado_oca=estado, cierre_alerta=cierre)
    return ResultadoConsulta(_consultado(actualizado, clasificacion, momento.ahora), cambio)


def registrar_error(envio: EnvioSeguido, mensaje: str, momento: MomentoConsulta) -> EnvioSeguido:
    """La consulta a OCA falló: queda el error y el envío se reclasifica con el último
    estado conocido (o sin datos) para que las reglas por fecha sigan al día. No toca el
    estado de OCA ni la fecha de la última consulta que respondió."""
    return replace(
        envio,
        clasificacion=_reclasificar(envio, momento.contexto),
        ultimo_error=ErrorConsulta(mensaje=mensaje, ocurrido_en=momento.ahora),
    )


def clave_estado(estado: EstadoOca) -> ClaveEstado:
    """`IdEstado`, estado, motivo, sucursal (textos normalizados; motivo vacío = "Sin
    Motivo") y `FechaEstado`: si alguno cambia, es un cambio de estado."""
    motivo = normalizar_texto(estado.motivo) or _SIN_MOTIVO_NORMALIZADO
    return (
        estado.id_estado,
        normalizar_texto(estado.estado),
        motivo,
        normalizar_texto(estado.sucursal_actual),
        estado.fecha_estado,
    )


def _remito_mas_viejo(despachos: Sequence[DespachoSiges]) -> DespachoSiges:
    if not despachos:
        raise ValueError("Hace falta al menos un remito para dar de alta un envío")
    guias = {despacho.guia for despacho in despachos}
    if len(guias) > 1:
        raise ValueError(f"Los remitos son de guías distintas: {', '.join(sorted(guias))}")
    return min(despachos, key=lambda despacho: (despacho.fecha_remito, despacho.id_remito))


def _reclasificar(envio: EnvioSeguido, contexto: ContextoClasificacion) -> ClasificacionEnvio:
    """Con el último estado conocido de OCA o, si nunca lo hubo, por la fecha del remito."""
    if envio.estado_oca is None:
        return clasificar_sin_datos(envio.fecha_remito, contexto)
    return clasificar_estado(envio.estado_oca, contexto)


def _consultado(
    envio: EnvioSeguido, clasificacion: ClasificacionEnvio, ahora: datetime
) -> EnvioSeguido:
    return replace(envio, clasificacion=clasificacion, consultado_en=ahora, ultimo_error=None)
