"""Puerto de solo lectura sobre request_validations (ventana de validación 0%).

La escritura/resolución de la ventana llega con el poller (paso posterior de la
migración); /load solo necesita saber si hay una validación PENDING (bloqueo 0) y la
nota de cambio de insumo para el detalle del Historial.
"""

from collections.abc import Sequence
from typing import Protocol

from src.modules.insumos.domain.value_objects.pending_validation import PendingValidation


class RequestValidationRepository(Protocol):
    async def get_pending(self, hp_request_id: int) -> PendingValidation | None:
        """La validación de esta solicitud SOLO si sigue PENDING."""
        ...

    async def get_swap_note(self, hp_request_id: int) -> str | None:
        """swap_note sin filtrar por status — se lee al crear el pedido, sea manual o
        autocarga (la nota va al Historial, nunca al texto del pedido en CD)."""
        ...

    async def get_pending_ids(self, hp_request_ids: Sequence[int]) -> set[int]:
        """Subset de los ids con validación todavía PENDING (badge "Validando")."""
        ...
