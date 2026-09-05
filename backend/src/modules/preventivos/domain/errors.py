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


class ZonaNoEncontradaError(NotFoundError):
    default_code = "ZONA_NO_ENCONTRADA"

    def __init__(self, zona: str) -> None:
        super().__init__(f"La zona {zona!r} no está en el catálogo de zonas de preventivos")


class CoordenadaFueraDeRangoError(ValidationError):
    default_code = "COORDENADA_FUERA_DE_RANGO"

    def __init__(self, latitud: float, longitud: float) -> None:
        super().__init__(
            f"Coordenada inválida: ({latitud}, {longitud}) fuera del rango de Argentina"
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
