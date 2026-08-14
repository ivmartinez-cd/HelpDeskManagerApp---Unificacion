"""Errores de dominio del módulo liquidaciones."""

from src.shared.domain.errors import ApplicationError, ExternalServiceError


class LiquidacionSinVinculoAyCError(ApplicationError):
    """La liquidación no tiene `numero_liquidacion` y no puede operarse en wsAyC."""

    default_code = "LIQUIDACION_SIN_VINCULO_AYC"

    def __init__(self, liquidacion_id: object) -> None:
        super().__init__(
            f"La liquidación {liquidacion_id} no tiene número AyC y no puede operarse "
            "en wsAyC. Solo disponible para liquidaciones importadas por sync SOAP."
        )


class LiquidacionAyCOperationError(ExternalServiceError):
    """El SOAP de wsAyC rechazó o no confirmó la operación de escritura."""

    default_code = "LIQUIDACION_AYC_OPERATION_ERROR"
