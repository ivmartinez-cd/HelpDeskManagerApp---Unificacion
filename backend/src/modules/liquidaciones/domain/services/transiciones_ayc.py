"""Transiciones válidas de estado hacia AyC (Recibir/Observar/Aprobar/Anular).

Puerto del comportamiento real de Web Agentes — el sistema real de Canal
Directo, no una suposición: `LiquidationsController::changeStatus/delete` +
`View/Liquidations/view.ctp` (repo `Web-Agentes`, mismo `estado_id` 1-5 que
esta app expone como `abierta`/`preliquidada`/`recibida`/`observada`/
`aprobada`/`cerrada`). Ahí cada botón solo se dibuja si el estado actual lo
permite (auditoría de liquidaciones, hallazgo "Botones de estado sin gating
por estado actual") — acá se replica esa misma condición, tanto para ocultar
el botón en la UI como para rechazar el request si igual llega.

No reproduce la restricción fina de Web Agentes por tipo de usuario (mesa de
ayuda vs. gerente, ej. Observar-desde-Aprobada era gerente-only): esta app no
modela esa distinción, ambos caen bajo el mismo permiso `liquidaciones.approve`.
"""

from src.modules.liquidaciones.domain.entities.liquidacion import (
    ESTADO_APROBADA,
    ESTADO_CERRADA,
    ESTADO_OBSERVADA,
    ESTADO_PRELIQUIDADA,
    ESTADO_RECIBIDA,
)
from src.modules.liquidaciones.domain.exceptions import TransicionEstadoAycInvalidaError

# Origen -> destino, ver view.ctp: Recibir (1,3)->2, Observar (2,4)->3, Aprobar (2,3)->4.
ORIGENES_VALIDOS_POR_VERBO = {
    "recibir": frozenset({ESTADO_PRELIQUIDADA, ESTADO_OBSERVADA}),
    "observar": frozenset({ESTADO_RECIBIDA, ESTADO_APROBADA}),
    "aprobar": frozenset({ESTADO_RECIBIDA, ESTADO_OBSERVADA}),
}


def validar_transicion(verbo: str, estado_actual: str) -> None:
    if estado_actual not in ORIGENES_VALIDOS_POR_VERBO[verbo]:
        raise TransicionEstadoAycInvalidaError(verbo, estado_actual)


def validar_anulable(estado_actual: str) -> None:
    """Eliminar/`voidLiquidation` en Web Agentes: el único estado que lo
    bloquea del todo es Cerrada — de ahí en más, algún rol de canal siempre
    puede (mesa de ayuda hasta Aprobada, gerente hasta Cerrada; acá no se
    distingue, así que se toma el máximo alcance: cualquier estado no cerrado)."""
    if estado_actual == ESTADO_CERRADA:
        raise TransicionEstadoAycInvalidaError("anular", estado_actual)
