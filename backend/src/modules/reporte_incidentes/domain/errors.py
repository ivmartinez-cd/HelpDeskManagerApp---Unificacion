from typing import ClassVar

from src.shared.domain.errors import ExternalServiceError, NotFoundError, ValidationError


class PeriodoInvalidoError(ValidationError):
    default_code: ClassVar[str] = "PERIODO_INVALIDO"

    def __init__(self, raw_value: str) -> None:
        super().__init__(f"Período inválido (se espera AAAA-MM): {raw_value!r}")


class EmpresaNoEncontradaError(NotFoundError):
    default_code: ClassVar[str] = "EMPRESA_NO_ENCONTRADA"

    def __init__(self, empresa_id: str) -> None:
        super().__init__(f"No existe un cliente activo con id {empresa_id!r}")


class IaNoConfiguradaError(ExternalServiceError):
    default_code: ClassVar[str] = "IA_NO_CONFIGURADA"

    def __init__(self) -> None:
        super().__init__(
            "La tipificación con IA no está configurada (falta GEMINI_API_KEY). "
            "Los incidentes sin tipificación guardada quedan pendientes de revisión."
        )


class TipificacionInvalidaError(ValidationError):
    default_code: ClassVar[str] = "TIPIFICACION_INVALIDA"


class CategoriaInvalidaError(ValidationError):
    default_code: ClassVar[str] = "CATEGORIA_INVALIDA"


class CategoriaNoEncontradaError(NotFoundError):
    default_code: ClassVar[str] = "CATEGORIA_NO_ENCONTRADA"

    def __init__(self, nombre: str) -> None:
        super().__init__(f"No existe la categoría {nombre!r}")
