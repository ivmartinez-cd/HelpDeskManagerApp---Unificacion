from typing import ClassVar
from uuid import UUID

from src.shared.domain.errors import BusinessRuleViolationError, NotFoundError, ValidationError


class LiquidacionNoEncontradaError(NotFoundError):
    default_code: ClassVar[str] = "LIQUIDACION_NO_ENCONTRADA"

    def __init__(self, liquidacion_id: UUID) -> None:
        super().__init__(f"Liquidación no encontrada: {liquidacion_id}")


class PrestadorNoEncontradoError(NotFoundError):
    default_code: ClassVar[str] = "PRESTADOR_NO_ENCONTRADO"

    def __init__(self, prestador_id: UUID) -> None:
        super().__init__(f"Prestador no encontrado: {prestador_id}")


class PrestadorConLiquidacionesError(BusinessRuleViolationError):
    """`liquidaciones.prestador_id` no tiene `ondelete` a propósito (ver
    `infrastructure/models/liquidacion_model.py`) — es historial de facturación
    real, no se pierde por una baja administrativa. Se traduce el
    `IntegrityError` de Postgres acá, en el repositorio, para no propagar un 500
    crudo."""

    default_code: ClassVar[str] = "PRESTADOR_CON_LIQUIDACIONES"

    def __init__(self, prestador_id: UUID) -> None:
        super().__init__(
            f"No se puede eliminar el prestador {prestador_id}: tiene liquidaciones "
            "asociadas. Desactivalo en su lugar."
        )


class ArchivoLiquidacionInvalidoError(ValidationError):
    """El archivo no se pudo leer como tabla, o ninguna tabla tiene una columna de
    incidente reconocible — mismo `ValueError` que el legacy convertía en 400."""

    default_code: ClassVar[str] = "ARCHIVO_LIQUIDACION_INVALIDO"

    def __init__(self, detalle: str) -> None:
        super().__init__(f"No se pudo leer el archivo de liquidación: {detalle}")


class ArchivoMaestroInvalidoError(ValidationError):
    """El archivo no se pudo leer como Excel, o ninguna hoja tiene una celda
    "AGENTE:" reconocible — mismo caso que el legacy convertía en 422 (acá 400,
    convención del monorepo para `ValidationError`)."""

    default_code: ClassVar[str] = "ARCHIVO_MAESTRO_INVALIDO"

    def __init__(self, detalle: str) -> None:
        super().__init__(f"No se pudo leer el archivo maestro de prestador: {detalle}")
