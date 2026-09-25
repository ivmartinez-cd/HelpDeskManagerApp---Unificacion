"""Parseo de las respuestas de wsAyC que usa el reporte (port de `normalize.ts`
y del mapeo de `incidents.ts`).

Cada operación devuelve un `xsd:string` con JSON adentro; cada fila viene
anidada bajo una clave (`Empresa`, `Incident`, `Instance`) y el servicio no es
consistente con los nombres de campo, por eso `elegir` prueba varias claves."""

import json
import logging
import re
from typing import Any

from src.modules.reporte_incidentes.domain.entities.incidente import (
    DetalleIncidente,
    Empresa,
    Trabajo,
)

logger = logging.getLogger(__name__)

# Placeholder de "sin restricción de servicio" en getEmpresas.
_SIN_RESTRICCION = "19990101"
_FECHA_DMY = re.compile(r"^(\d{2})/(\d{2})/(\d{4})")
Fila = dict[str, Any]


def parse_json(raw: object, operacion: str) -> Any:
    """JSON embebido en la respuesta; None si viene vacía o no parsea."""
    texto = "" if raw is None else str(raw).strip()
    if not texto:
        return None
    try:
        return json.loads(texto)
    except ValueError:
        logger.warning("wsAyC %s: respuesta no es JSON", operacion, extra={"operacion": operacion})
        return None


def filas(raw: object, operacion: str, clave: str) -> list[Fila]:
    parsed = parse_json(raw, operacion)
    items = parsed if isinstance(parsed, list) else []
    return [desenvolver(f, clave) for f in items if isinstance(f, dict)]


def desenvolver(fila: Fila, clave: str) -> Fila:
    interior = fila.get(clave)
    return interior if isinstance(interior, dict) else fila


def elegir(fila: Fila, claves: tuple[str, ...]) -> str | None:
    """Primer valor no vacío entre las claves (probando también minúsculas/mayúsculas)."""
    for clave in claves:
        for variante in (clave, clave.lower(), clave.upper()):
            valor = fila.get(variante)
            if valor is not None and str(valor).strip():
                return str(valor).strip()
    return None


def es_vacio(valor: str | None) -> bool:
    """El servicio rellena vacíos con " ", "-", "," o "."."""
    return valor is None or re.sub(r"[\s,.\-]", "", valor) == ""


def fecha_iso(raw: str | None) -> str:
    """`DD/MM/AAAA[ hh:mm:ss]` → `AAAA-MM-DD`; 1900-01-01 (sin fecha) → ""."""
    if not raw:
        return ""
    texto = raw.strip()
    if texto.startswith(("01/01/1900", "1900-01-01")):
        return ""
    match = _FECHA_DMY.match(texto)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    return texto[:10]


def _limpio(valor: str | None) -> str | None:
    return None if es_vacio(valor) else (valor or "").strip()


def trabajo(fila: Fila) -> Trabajo:
    return Trabajo(
        descripcion=_limpio(elegir(fila, ("Tareas", "Descripcion"))) or "",
        observ=_limpio(elegir(fila, ("Observaciones", "Observ", "Observacion"))),
        fecha=_limpio(elegir(fila, ("Fecha",))),
        estado=_limpio(elegir(fila, ("Estado", "EstadoWeb"))),
        tecnico=_limpio(elegir(fila, ("Tecnico",))),
    )


def trabajos(raw: object) -> list[Trabajo]:
    """Sin filas vacías y en orden cronológico (el servicio las devuelve al revés)."""
    todos = [trabajo(f) for f in filas(raw, "getIncidentInstances", "Instance")]
    con_contenido = [t for t in todos if t.descripcion or t.observ or t.estado or t.fecha]
    return list(reversed(con_contenido))


def detalle(raw: object) -> DetalleIncidente:
    parsed = parse_json(raw, "getIncidentById")
    nodo = parsed[0] if isinstance(parsed, list) and parsed else parsed
    fila = desenvolver(nodo, "Incident") if isinstance(nodo, dict) else {}
    return DetalleIncidente(
        causa=elegir(fila, ("Causa",)),
        tecnico=elegir(fila, ("Tecnico", "Prestador")),
        fecha_cierre=fecha_iso(elegir(fila, ("FechaCierre", "fecha_cierre"))) or None,
        tipo_trabajo=elegir(fila, ("Tipo",)),
    )


def empresa_activa(fila: Fila, hoy_aaaammdd: str) -> Empresa | None:
    """Activa si la restricción es el placeholder o una fecha que no pasó."""
    restriccion = elegir(fila, ("FechaRestriccionServicio",)) or _SIN_RESTRICCION
    empresa_id = elegir(fila, ("id", "IdEmpresa", "empresa_id"))
    if not empresa_id:
        return None
    if restriccion != _SIN_RESTRICCION and restriccion < hoy_aaaammdd:
        return None
    nombre = elegir(fila, ("Nombre", "RazonSocial", "razon_social", "name")) or "—"
    return Empresa(empresa_id, nombre)
