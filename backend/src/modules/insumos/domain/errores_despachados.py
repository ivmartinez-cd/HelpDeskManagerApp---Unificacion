"""Errores de Insumos > Despachados (aparte de `errors.py`, que ya está cerca del
límite de tamaño de §4)."""

from src.shared.domain.errors import (
    BusinessRuleViolationError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)


class RespuestaOcaInvalidaError(ExternalServiceError):
    """OCA respondió algo que no se puede interpretar como un estado de envío
    (XML mal formado, `FechaEstado` o `IdEstado` ilegibles)."""

    default_code = "RESPUESTA_OCA_INVALIDA"

    def __init__(self, guia: str, detalle: str) -> None:
        super().__init__(f"Respuesta inválida de OCA para la guía {guia}: {detalle}")


class SincronizacionDespachosEnCursoError(BusinessRuleViolationError):
    """Ya hay una actualización corriendo (el job programado o "Actualizar ahora"): la
    que está en curso termina sola, no hay que reintentar."""

    default_code = "SINCRONIZACION_DESPACHOS_EN_CURSO"

    def __init__(self) -> None:
        super().__init__("Ya hay una actualización de Despachados en curso")


class EnvioDespachoNoEncontradoError(NotFoundError):
    default_code = "ENVIO_DESPACHO_NO_ENCONTRADO"

    def __init__(self, guia: str) -> None:
        super().__init__(f"No hay un envío OCA seguido con la guía {guia}")


class AccionDespachoInvalidaError(ValidationError):
    """El detalle de la acción está vacío o es demasiado largo."""

    default_code = "ACCION_DESPACHO_INVALIDA"


class AlertaDespachoNoAbiertaError(BusinessRuleViolationError):
    default_code = "ALERTA_DESPACHO_NO_ABIERTA"

    def __init__(self, guia: str) -> None:
        super().__init__(f"La guía {guia} no tiene una alerta abierta")


class CierreAlertaSinAccionError(BusinessRuleViolationError):
    """Una alerta solo se cierra después de registrar al menos una acción."""

    default_code = "CIERRE_ALERTA_SIN_ACCION"

    def __init__(self, guia: str) -> None:
        super().__init__(f"Registrá una acción sobre la guía {guia} antes de cerrar su alerta")
