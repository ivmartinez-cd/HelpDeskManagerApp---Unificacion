"""Deep-links al PortalWeb de SDS — port de portal_web_base_url/device_portal_url.

El PortalWeb (UI) es hermano del PortalAPI (API) en el mismo host: la base sale de
recortarle el sufijo a la URL de la API, no de una segunda variable de entorno que
podría quedar desincronizada.
"""

_API_SUFFIX = "/PortalAPI"
_WEB_SUFFIX = "/PortalWeb"


def portal_web_base_url(insight_base_url: str) -> str:
    return insight_base_url.rstrip("/").removesuffix(_API_SUFFIX) + _WEB_SUFFIX


def device_portal_url(insight_base_url: str, device_id: int) -> str:
    """Ficha del equipo. El deep-link al consumible puntual del portal no funciona
    fuera de su propio JS (link `only-ajax`), así que esta es la URL más específica
    que se puede ofrecer desde afuera."""
    return f"{portal_web_base_url(insight_base_url)}/devices/{device_id}"


def device_registration_url(insight_base_url: str, device_id: int) -> str:
    """Formulario de registro del equipo — el único lugar donde un equipo descubierto
    pasa a monitoreado y deja de aparecer como "sin registrar"."""
    base = portal_web_base_url(insight_base_url)
    return f"{base}/asset-registration?step=1&action=edit&d={device_id}"
