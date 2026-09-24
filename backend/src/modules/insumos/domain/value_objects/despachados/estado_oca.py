"""Último estado de un envío según OCA (`GetEnvioEstadoActual` del webservice e-Pak).

Se guardan los campos tal como llegan (con espacios recortados): la
interpretación (color, alerta, cierre) es de `domain/services/despachados/semaforo.py`.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class EstadoOca:
    numero_envio: str
    operativa: str
    """434324 a domicilio; 434305 y 443913 a domicilio con rendición de acuse; 436233."""
    orden_retiro: str
    sucursal_actual: str
    fecha_estado: date
    """`FechaEstado` (dd/mm/aaaa, sin hora)."""
    estado: str
    """Texto del estado ("Entregado", "Acuse en Rendicion", …)."""
    id_estado: int | None
    """`IdEstado`; None cuando OCA no lo informa (los estados de acuse llegan así)."""
    motivo: str
    """Tal cual llega; "" si vino vacío (las reglas lo tratan como "Sin Motivo")."""
    cantidad_paquetes: int | None
