"""Errores de dominio del módulo liquidaciones."""

from src.shared.domain.errors import (
    ApplicationError,
    BusinessRuleViolationError,
    ExternalServiceError,
)


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


class LiquidacionConVinculoAycError(BusinessRuleViolationError):
    """La liquidación tiene `numero_liquidacion` — su estado lo gobierna AyC
    (reconciliación automática, ver ADR-024, o los botones Aprobar/Observar/
    Anular), nunca un cambio manual local. Sin este guard, un cambio a mano
    quedaría revertido en la próxima reconciliación sin aviso."""

    default_code = "LIQUIDACION_CON_VINCULO_AYC"

    def __init__(self, liquidacion_id: object) -> None:
        super().__init__(
            f"La liquidación {liquidacion_id} está vinculada a Canal Directo — su "
            "estado se actualiza solo, contra AyC. Usá los botones Aprobar/Observar/"
            "Anular para cambiarlo a mano."
        )
