"""Comentario sugerido para reclamar un envío en OCA: lo que HDM sabe de la guía (estado y
motivo de OCA, sucursal, fechas, cliente, incidentes, remitos y bultos), en líneas cortas
para pegar en el formulario de grandes cuentas. El operador lo revisa antes de enviarlo."""

from collections.abc import Sequence
from datetime import date

from src.modules.insumos.domain.entities.despachados.envio_seguido import EnvioSeguido
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import DespachoSiges
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca

_SIN_MOTIVO = "sin motivo"
_CIERRE = "Pedimos revisar el envío y confirmar cómo sigue la entrega."


def comentario_reclamo(envio: EnvioSeguido, remitos: Sequence[DespachoSiges]) -> str:
    """Una línea por dato; las que no aplican (sin motivo, sin límite, sin incidentes) no
    aparecen."""
    lineas = [
        f"Reclamo por el envío {envio.guia}.",
        _linea_estado(envio.estado_oca),
        _linea_limite(envio),
        _linea_cliente(envio),
        _linea_incidentes(remitos),
        _linea_remitos(remitos),
        _CIERRE,
    ]
    return "\n".join(linea for linea in lineas if linea)


def _fecha(dia: date) -> str:
    return dia.strftime("%d/%m/%Y")


def _linea_estado(estado: EstadoOca | None) -> str:
    if estado is None:
        return "OCA todavía no informa ningún estado para esta guía."
    texto = f"Estado en OCA: {estado.estado}"
    if estado.motivo and estado.motivo.strip().lower() != _SIN_MOTIVO:
        texto += f" (motivo: {estado.motivo})"
    texto += f", desde el {_fecha(estado.fecha_estado)}"
    if estado.sucursal_actual:
        texto += f", sucursal {estado.sucursal_actual}"
    return texto + "."


def _linea_limite(envio: EnvioSeguido) -> str:
    limite = envio.clasificacion.fecha_limite
    if envio.clasificacion.color is not ColorSemaforo.ROJO or limite is None:
        return ""
    return f"Fecha límite de retiro en sucursal: {_fecha(limite)}."


def _linea_cliente(envio: EnvioSeguido) -> str:
    if envio.sucursal_cliente:
        return f"Cliente: {envio.cliente} ({envio.sucursal_cliente})."
    return f"Cliente: {envio.cliente}."


def _linea_incidentes(remitos: Sequence[DespachoSiges]) -> str:
    numeros = list(dict.fromkeys(i.numero for r in remitos for i in r.incidentes))
    if not numeros:
        return ""
    etiqueta = "Incidentes" if len(numeros) > 1 else "Incidente"
    return f"{etiqueta}: {', '.join(numeros)}."


def _linea_remitos(remitos: Sequence[DespachoSiges]) -> str:
    if not remitos:
        return ""
    etiqueta = "Remitos" if len(remitos) > 1 else "Remito"
    partes = [f"{r.numero_remito} ({r.bultos} {_bultos(r.bultos)})" for r in remitos]
    return f"{etiqueta}: {', '.join(partes)}."


def _bultos(cantidad: int) -> str:
    return "bulto" if cantidad == 1 else "bultos"
