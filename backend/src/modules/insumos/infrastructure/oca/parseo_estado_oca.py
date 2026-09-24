"""Parseo de la respuesta de `GetEnvioEstadoActual` (webservice e-Pak de OCA).

OCA devuelve un DataSet de .NET serializado: un `xs:schema` que describe las columnas
(ahí "Table" aparece solo como valor del atributo `name`, nunca como elemento) y un
diffgram con `<NewDataSet xmlns=""><Table>…</Table></NewDataSet>`. La fila es el primer
elemento `Table`; si OCA no conoce la guía, el DataSet llega sin ninguno. `Table` y sus
campos se buscan por nombre local (`{*}`) para no depender de que `NewDataSet` siga
redefiniendo el `xmlns="#Oca_e_Pak"` del DataSet externo.

ElementTree de la stdlib alcanza para XML externo: desde expat 2.4.1 (la imagen trae la
2.8.3) la expansión de entidades está acotada, sin sumar defusedxml como dependencia.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime

from src.modules.insumos.domain.errores_despachados import RespuestaOcaInvalidaError
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca

logger = logging.getLogger(__name__)

_FORMATO_FECHA_ESTADO = "%d/%m/%Y"
# `DataSet` es la respuesta real; `NewDataSet` suelto es la forma recortada del brief.
_RAICES_DATASET = frozenset({"DataSet", "NewDataSet"})
_LARGO_INICIO = 160


def parsear_estado_actual(contenido: bytes, guia: str) -> EstadoOca | None:
    """Último estado del envío, o None si OCA no devolvió ninguna fila para la guía.

    Lanza `RespuestaOcaInvalidaError` si el XML está mal formado, si no es un DataSet de
    OCA o si `FechaEstado` o `IdEstado` no se pueden leer."""
    campos = _campos_de_la_fila(contenido, guia)
    if campos is None:
        return None
    return EstadoOca(
        numero_envio=campos.get("NumeroEnvio") or guia,
        operativa=campos.get("Operativa", ""),
        orden_retiro=campos.get("OrdenRetiro", ""),
        sucursal_actual=campos.get("SucursalActual", ""),
        fecha_estado=_fecha_estado(campos.get("FechaEstado", ""), guia),
        estado=campos.get("Estado", ""),
        id_estado=_id_estado(campos.get("IdEstado", ""), guia),
        motivo=campos.get("Motivo", ""),
        cantidad_paquetes=_cantidad_paquetes(campos.get("CantidadPaquetes", ""), guia),
    )


def _campos_de_la_fila(contenido: bytes, guia: str) -> dict[str, str] | None:
    """Campos de la primera `Table` por nombre local, con el texto recortado.

    Solo un DataSet sin filas significa "OCA no conoce la guía": cualquier otro XML (una
    página del proxy, un error de IIS) es una respuesta inválida, no un envío sin datos."""
    try:
        raiz = ET.fromstring(contenido)
    except ET.ParseError as exc:
        detalle = f"XML mal formado ({exc}): {_inicio(contenido)}"
        raise RespuestaOcaInvalidaError(guia, detalle) from exc
    if _nombre_local(raiz.tag) not in _RAICES_DATASET:
        raise RespuestaOcaInvalidaError(guia, f"no es un DataSet de OCA: {_inicio(contenido)}")
    fila = raiz.find(".//{*}Table")
    if fila is None:
        return None
    return {_nombre_local(campo.tag): (campo.text or "").strip() for campo in fila}


def _inicio(contenido: bytes) -> str:
    """Comienzo de una respuesta que no es un DataSet de OCA, para diagnosticar (no trae
    datos del destinatario: esos solo viajan dentro de la `Table`)."""
    return repr(contenido[:_LARGO_INICIO].decode("utf-8", errors="replace"))


def _nombre_local(etiqueta: str) -> str:
    return etiqueta.rsplit("}", 1)[-1]


def _fecha_estado(texto: str, guia: str) -> date:
    try:
        return datetime.strptime(texto, _FORMATO_FECHA_ESTADO).date()
    except ValueError as exc:
        raise RespuestaOcaInvalidaError(guia, f"FechaEstado ilegible: {texto!r}") from exc


def _id_estado(texto: str, guia: str) -> int | None:
    """None si OCA no lo informa (los estados de acuse llegan sin `IdEstado`)."""
    if not texto:
        return None
    try:
        return int(texto)
    except ValueError as exc:
        raise RespuestaOcaInvalidaError(guia, f"IdEstado no numérico: {texto!r}") from exc


def _cantidad_paquetes(texto: str, guia: str) -> int | None:
    """Dato informativo: si viene vacío o ilegible no invalida el estado."""
    if not texto:
        return None
    try:
        return int(texto)
    except ValueError:
        logger.warning("OCA informó CantidadPaquetes ilegible %r para la guía %s", texto, guia)
        return None
