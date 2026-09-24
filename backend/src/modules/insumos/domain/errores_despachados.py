"""Errores de Insumos > Despachados (aparte de `errors.py`, que ya está cerca del
límite de tamaño de §4)."""

from src.shared.domain.errors import ExternalServiceError


class RespuestaOcaInvalidaError(ExternalServiceError):
    """OCA respondió algo que no se puede interpretar como un estado de envío
    (XML mal formado, `FechaEstado` o `IdEstado` ilegibles)."""

    default_code = "RESPUESTA_OCA_INVALIDA"

    def __init__(self, guia: str, detalle: str) -> None:
        super().__init__(f"Respuesta inválida de OCA para la guía {guia}: {detalle}")
