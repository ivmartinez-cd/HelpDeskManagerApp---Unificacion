"""Puerto sobre request_validations (ventana de validación 0%).

Lectura: /load solo necesita saber si hay una validación PENDING (bloqueo 0) y la
nota de cambio de insumo para el detalle del Historial; list_requests pinta el badge
"Validando". Escritura/resolución: la orquesta validation_window.py (llamada desde
list_requests y, cuando llegue el poller, desde la autocarga).
"""

from collections.abc import Sequence
from typing import Protocol

from src.modules.insumos.domain.value_objects.pending_validation import (
    PendingValidation,
    PendingValidationWork,
    ValidationStart,
)


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

    async def get_pending_batch(
        self, hp_request_ids: Sequence[int]
    ) -> dict[int, PendingValidation]:
        """Las validaciones PENDING completas para estos ids (badge + tooltip)."""
        ...

    async def is_diagnosed(self, hp_request_id: int) -> bool:
        """True si la fila existe y ya tiene el diagnóstico calculado (swap_checked) —
        el gate para no volver a consultar Insight en cada ciclo/vista. False si la
        fila no existe o quedó de una versión sin diagnóstico."""
        ...

    async def start(self, data: ValidationStart) -> None:
        """Arranca la ventana (status PENDING, deadline = ahora + deadline_minutes), o
        si la fila ya existe completa swap_note/diagnosis_* SIN reiniciar el reloj ni
        pisar un status ya resuelto — y solo si todavía no se había diagnosticado
        (cubre filas creadas por una versión anterior sin diagnóstico automático)."""
        ...

    async def resolve(self, hp_request_id: int, status: str) -> bool:
        """Transiciona PENDING -> CONFIRMED | DISMISSED. Devuelve True solo si ESTA
        llamada hizo la transición (WHERE status='PENDING'): seguro ante la carrera
        entre el poller de fondo y una lectura del dashboard resolviendo la misma fila
        casi a la vez — el caller lo usa para no duplicar el evento AUTO_DISMISSED."""
        ...

    async def get_all_pending(self) -> list[PendingValidationWork]:
        """Todas las filas PENDING, sin filtrar por deadline — resolve_pending las
        re-chequea contra el nivel en vivo en CADA ciclo (no solo al vencer el reloj),
        para descartar apenas se recupera. `is_due` viene calculado en SQL."""
        ...
