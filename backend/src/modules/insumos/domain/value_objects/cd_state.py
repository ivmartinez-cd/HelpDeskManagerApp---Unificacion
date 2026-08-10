"""Ciclo de vida del campo `Estado` de un supply en Canal Directo (getSupplyById).

Portado de `cd_states.py` del legacy, verificado contra producción (`Estado` real de 246
pedidos activos): Pendiente, Despachado, Remito Generado, Entregado, Anulado. El filtro de
"¿sigue en tránsito?" es lista negra (estado NOT IN terminales), nunca una whitelist de los
estados conocidos: si Canal Directo agrega mañana un estado intermedio que no anticipamos
acá, el pedido no debe desaparecer en silencio de la vista de seguimiento (ese fue el bug
original: Despachado/Remito Generado no estaban en la whitelist implícita `== "Pendiente"`
y el pedido dejaba de verse en cualquier lado).
"""

PENDIENTE = "Pendiente"
DESPACHADO = "Despachado"
REMITO_GENERADO = "Remito Generado"
ENTREGADO = "Entregado"
ANULADO = "Anulado"
CANCELADO = "Cancelado"

# Orden del ciclo de vida — solo para presentación (timeline), nunca para filtrar.
LIFECYCLE = (PENDIENTE, REMITO_GENERADO, DESPACHADO, ENTREGADO)

# Ya no está "en curso".
INACTIVE_STATES = (ENTREGADO, ANULADO, CANCELADO)

# Estados que liberan la solicitud (permiten volver a cargar un pedido para la misma
# serie+sku) — Entregado NO libera: es un cierre exitoso, no una anulación.
RELEASE_STATES = frozenset({ANULADO, CANCELADO})


def is_in_transit(estado: str | None) -> bool:
    """True si el pedido sigue circulando en CD (fail-open: cualquier estado no terminal)."""
    return bool(estado) and estado not in INACTIVE_STATES
