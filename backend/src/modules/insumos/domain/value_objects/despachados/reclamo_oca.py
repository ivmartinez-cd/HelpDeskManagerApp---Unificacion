"""Datos para reclamar un envío en OCA desde su formulario público de grandes cuentas.

HDM no reclama por API (OCA no tiene una): prepara lo que el operador tiene que cargar en
el formulario (contacto de la cuenta de Canal Directo que despachó, guía y un comentario
con lo que HDM sabe del envío) y el operador lo revisa y lo envía él mismo.

La cuenta de OCA que despachó se reconoce por el prefijo de la guía (26108… = 434324 OCA
CORREO, 211… = 443913 OCA CLIENTE; ver `DespachadosSettings.oca_reclamo_contactos`).
"""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContactoReclamoOca:
    """Quién reclama: los datos de la cuenta de Canal Directo en OCA."""

    nombre: str
    apellido: str
    empresa: str
    email: str
    cuit: str
    """Solo dígitos, sin guiones (así lo pide el formulario)."""
    telefono: str
    """"" si la cuenta no tiene uno cargado."""


@dataclass(frozen=True, slots=True)
class ReglaContactoReclamo:
    """Las guías que empiezan con `prefijo` se reclaman con `contacto`."""

    prefijo: str
    cuenta: str
    """Cuenta/operativa de OCA a la que corresponde, para quien lee la configuración."""
    contacto: ContactoReclamoOca


@dataclass(frozen=True, slots=True)
class ReclamoOca:
    guia: str
    operativa: str
    """La última que informó OCA; "" si OCA todavía no registra la guía."""
    contacto: ContactoReclamoOca | None
    """None si ninguna regla reconoce el prefijo de la guía."""
    comentario: str
    """Texto sugerido para el comentario del formulario; el operador lo puede editar."""


def contacto_para_guia(
    guia: str, reglas: Sequence[ReglaContactoReclamo]
) -> ContactoReclamoOca | None:
    """Contacto de la regla cuyo prefijo coincide con la guía; si coinciden varias, gana la
    de prefijo más largo. None si ninguna coincide (o si el prefijo está vacío)."""
    candidatas = [r for r in reglas if r.prefijo and guia.startswith(r.prefijo)]
    if not candidatas:
        return None
    return max(candidatas, key=lambda regla: len(regla.prefijo)).contacto
