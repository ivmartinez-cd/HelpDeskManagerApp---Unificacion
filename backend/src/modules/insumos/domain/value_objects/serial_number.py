"""Normalización de números de serie y extracción del serial en pedidos de origen interno.

Portado de `soap_query.py` del legacy (clean_serial, _INTERNAL_SERIAL_RE,
extract_serial_from_supply), con los mismos casos reales documentados.
"""

import re

# Artefactos de formato que a veces trae el serial de Insight pero no forman parte del
# serial real en Canal Directo — medido en producción: Insight guarda "Z83DBJEJ90000GT."
# (con punto final) mientras que CD tiene "Z83DBJEJ90000GT" sin punto, y getMachineBySerial
# hace match exacto: el punto de más hacía que el SOAP devolviera "[]" (falso BODEGA) para
# un equipo que en realidad seguía asignado a un cliente.
_SERIAL_ARTIFACT_CHARS = " .\t\r\n"

# Serial en el campo NroSerie de órdenes de origen interno. Formatos observados:
#   Formato A: "MXBCQ8Z0K6  Porcentaje: 10\nDias Restantes Est.: 3"  (serial al inicio)
#   Formato B: "Porcentaje: 6\nDias Restantes Est.: 10\nPHC5R19633"  (serial al final)
#   Formato C: "0BLQBJKJ90000JV   "  (solo el serial, sin texto extra — y puede empezar con dígito)
# Estrategia: buscar el primer "token" de ≥5 chars compuesto SOLO de mayúsculas/dígitos
# que contenga al menos una letra (para no matchear los números sueltos de "Porcentaje"/
# "Dias Restantes", que siempre son cortos). No exigimos que arranque con letra: algunos
# seriales (ej. impresoras Samsung) arrancan con dígito, y \b no separa "0" de "B" porque
# ambos son \w — con [A-Z] al inicio el regex nunca los matcheaba (bug real: supply 441396).
_INTERNAL_SERIAL_RE = re.compile(r"\b(?=[A-Z0-9]*[A-Z])([A-Z0-9]{5,})\b", re.ASCII)


def clean_serial(serial: str | None) -> str:
    """Saca espacios/puntos/tabs/saltos de línea sobrantes de un número de serie."""
    return (serial or "").strip(_SERIAL_ARTIFACT_CHARS)


def extract_internal_serial(nro_serie: str | None) -> str:
    """Extrae el serial del texto libre de NroSerie de un pedido de origen interno."""
    match = _INTERNAL_SERIAL_RE.search(nro_serie or "")
    return match.group(1).upper() if match else ""


def serial_from_supply_fields(nro_serie_solicitud: str | None, nro_serie: str | None) -> str:
    """Serial de la máquina de un supply de Canal Directo.

    Para órdenes normales: NroSerieSolicitud (ej. "MXBCQ8Z0K6"). Para órdenes de origen
    interno NroSerieSolicitud viene vacío y el serial hay que extraerlo del texto libre
    de NroSerie (ver formatos en _INTERNAL_SERIAL_RE).
    """
    serial = (nro_serie_solicitud or "").strip().upper()
    if serial:
        return serial
    return extract_internal_serial(nro_serie)
