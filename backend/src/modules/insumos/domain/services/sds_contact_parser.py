"""Parseo del comentario libre de un equipo en SDS Insight para extraer contacto.

El formato es convención interna de Canal Directo SA, no un estándar del portal.
Ejemplo real:
    Contacto: German Brega
    Mail: gbrega@empresa.com
    CARGAR PARA SUCURSAL: Casa Central
"""

import re

from src.modules.insumos.domain.value_objects.zone_contacts import SdsContactRow

_CONTACTO_RE = re.compile(r"^Contacto:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
_MAIL_RE = re.compile(r"^Mail:\s*(\S+)", re.IGNORECASE | re.MULTILINE)
_SUCURSAL_RE = re.compile(
    r"CARGAR PARA SUCURSAL:\s*(.+?)\.?\s*$", re.IGNORECASE | re.MULTILINE
)


def parse_sds_contact_comment(
    zone: str, comment: str | None
) -> SdsContactRow | None:
    """Extrae contacto/mail/sucursal del comentario de un equipo.

    Devuelve None si el comentario no tiene la línea "Contacto:".
    """
    if not comment:
        return None
    contacto_match = _CONTACTO_RE.search(comment)
    if contacto_match is None:
        return None
    sucursal_match = _SUCURSAL_RE.search(comment)
    mail_match = _MAIL_RE.search(comment)
    return SdsContactRow(
        zone=zone,
        contacto=contacto_match.group(1),
        email=mail_match.group(1) if mail_match else "",
        sucursal=sucursal_match.group(1) if sucursal_match else "",
    )
