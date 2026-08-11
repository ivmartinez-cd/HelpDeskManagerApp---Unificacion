"""DTOs de la pantalla de equipos sin registrar."""

from dataclasses import dataclass

from src.modules.insumos.domain.entities.known_device import KnownDevice


@dataclass(frozen=True)
class NewDeviceRow:
    """El equipo más el link directo al formulario de registro del portal: es la única
    acción posible sobre esta pantalla, y armarlo a mano en el frontend duplicaría la
    convención de URLs del portal."""

    device: KnownDevice
    registration_url: str
