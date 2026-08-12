from typing import ClassVar
from uuid import UUID

from src.shared.domain.errors import NotFoundError


class LiquidacionNoEncontradaError(NotFoundError):
    default_code: ClassVar[str] = "LIQUIDACION_NO_ENCONTRADA"

    def __init__(self, liquidacion_id: UUID) -> None:
        super().__init__(f"Liquidación no encontrada: {liquidacion_id}")
