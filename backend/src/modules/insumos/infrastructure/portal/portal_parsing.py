"""Parsing puro del HTML del PortalWeb de SDS — sin I/O, sin estado."""

import html
import re

from src.modules.insumos.domain.value_objects.order_request import ContactInfo

_CSRF_TOKEN_RE = re.compile(r'name="__csrftoken"\s+value="([^"]+)"')
DELETE_SUCCESS_MARKER = "Los cambios se han guardado correctamente"
MAX_HTML_BYTES = 5 * 1024 * 1024

_DETAILS_SECTION_RE = re.compile(
    r'<section id="deliveryLocationDetails">(.*?)</section>', re.S
)
_CONTACT_NAME_RE = re.compile(
    r"<th>\s*Nombre de la persona de contacto\s*</th>\s*<td>(.*?)</td>", re.S
)
_CONTACT_EMAIL_RE = re.compile(
    r"<th>\s*Correo electrónico de contacto\s*</th>\s*<td>(.*?)</td>", re.S
)
_CONTACT_PHONE_RE = re.compile(
    r"<th>\s*Teléfono de contacto\s*</th>\s*<td>(.*?)</td>", re.S
)
_TAG_RE = re.compile(r"<[^>]+>")


def _clean_cell(cell_html: str) -> str:
    return html.unescape(_TAG_RE.sub("", cell_html)).strip()


def extract_csrf_token(html_content: str) -> str | None:
    """Token CSRF del formulario de baja. None si no está (señal de sesión vencida
    o de que el formulario no está disponible por otro motivo — ver delete_device)."""
    m = _CSRF_TOKEN_RE.search(html_content)
    return m.group(1) if m else None


def is_delete_success(response_body: str) -> bool:
    return DELETE_SUCCESS_MARKER in response_body


def parse_delivery_location_contact(
    html_content: str, location_id: int | str
) -> ContactInfo | None:
    """Extrae el contacto de la página de detalle de una delivery location.

    Devuelve None si la ubicación no tiene contacto. Lanza ValueError si no se
    encuentra la sección de detalle esperada (señal de que cambió la estructura
    del portal).
    """
    section_match = _DETAILS_SECTION_RE.search(html_content)
    if section_match is None:
        raise ValueError(
            f"Delivery location {location_id}: no se encontró la sección de detalle "
            "en el HTML del PortalWeb (¿cambió la estructura del portal?)"
        )
    section = section_match.group(1)
    name_match = _CONTACT_NAME_RE.search(section)
    name = _clean_cell(name_match.group(1)) if name_match else ""
    if not name:
        return None
    email = _clean_cell(m.group(1)) if (m := _CONTACT_EMAIL_RE.search(section)) else ""
    phone = _clean_cell(m.group(1)) if (m := _CONTACT_PHONE_RE.search(section)) else ""
    if name.count(",") == 1:
        apellido, nombre = (part.strip() for part in name.split(","))
    else:
        apellido, nombre = name, ""
    return ContactInfo(apellido=apellido, nombre=nombre, telefono=phone, email=email)
