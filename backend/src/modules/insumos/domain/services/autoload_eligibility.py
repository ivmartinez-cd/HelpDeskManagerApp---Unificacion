"""Criterio de "urgente" compartido por autocarga y dashboard — port de
is_autoload_eligible/needs_validation de api_helpers.py."""


def is_autoload_eligible(
    days_left: int, percent_left: float, max_days: int, min_percent: int
) -> bool:
    """Mismo criterio en toda la app: lo usa la autocarga para decidir si crea el
    pedido (o lo deja pasar por la ventana de validación primero, ver
    needs_validation) y list_requests para decidir si mostrarla como candidata."""
    return days_left <= max_days or percent_left <= min_percent


def needs_validation(percent_left: float) -> bool:
    """True si una solicitud elegible (is_autoload_eligible) debe pasar por la ventana
    de validación antes de autocargarse o poder cargarse a mano.

    Acotado a percentLeft == 0: es el único patrón que reprodujo el glitch de sensor
    real (equipo MXBCQ7C03T, ago-2026) que motivó la ventana. Una solicitud que ya
    venía bajando gradualmente (ej. 5%, o daysLeft corto con % normal) es una alerta
    legítima de HP SDS, no hace falta reconfirmarla contra el nivel en vivo."""
    return percent_left == 0
