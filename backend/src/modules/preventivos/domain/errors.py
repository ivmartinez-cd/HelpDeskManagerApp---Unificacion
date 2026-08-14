from src.shared.domain.errors import (
    BusinessRuleViolationError,
    NotFoundError,
    ValidationError,
)


class ZonaInvalidaError(ValidationError):
    default_code = "ZONA_INVALIDA"

    def __init__(self, zona: str) -> None:
        super().__init__(
            f"Zona inválida: {zona!r} (vacía o fuera del alcance de preventivos locales)"
        )


class HabilitacionYaActivaError(BusinessRuleViolationError):
    default_code = "HABILITACION_YA_ACTIVA"

    def __init__(self, siges_maquina_id: int) -> None:
        super().__init__(
            f"La máquina {siges_maquina_id} ya tiene una habilitación de preventivo activa"
        )


class HabilitacionNoEncontradaError(NotFoundError):
    default_code = "HABILITACION_NO_ENCONTRADA"

    def __init__(self, siges_maquina_id: int) -> None:
        super().__init__(
            f"La máquina {siges_maquina_id} no tiene una habilitación de preventivo activa"
        )
