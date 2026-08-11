from typing import ClassVar

from src.shared.domain.errors import (
    BusinessRuleViolationError,
    ExternalServiceError,
    ValidationError,
)


class RangoDeEstadisticasInvalidoError(ValidationError):
    """Rango de fechas incoherente en /estadisticas. 422 (y no el 400 default de
    ValidationError) para preservar el contrato del legacy, que devolvía 422 tanto
    para el formato de fecha como para el rango invertido."""

    http_status: ClassVar[int] = 422
    default_code: ClassVar[str] = "RANGO_DE_ESTADISTICAS_INVALIDO"


class SerieNoActivaEnCanalDirectoError(BusinessRuleViolationError):
    """getMachineBySerial no resolvió la familia de consumibles: la serie no existe
    en Canal Directo o el modelo no tiene familia asignada (típico: equipo dado de
    baja o reasignado a bodega)."""

    default_code = "SERIE_NO_ACTIVA_EN_CANAL_DIRECTO"

    def __init__(self, device_serial: str) -> None:
        super().__init__(
            f"Canal Directo no pudo resolver la familia de consumibles para la serie "
            f"{device_serial} (¿la serie no existe en Canal Directo o el modelo no "
            "tiene familia asignada?)"
        )


class FamiliaSinInsumosError(BusinessRuleViolationError):
    """La familia del equipo existe en Canal Directo pero no tiene insumos cargados."""

    default_code = "FAMILIA_SIN_INSUMOS"

    def __init__(self, familia_name: str, device_serial: str) -> None:
        super().__init__(
            f"No hay insumos configurados en Canal Directo para la familia "
            f"'{familia_name}' (serie {device_serial})"
        )


class InsumoAmbiguoError(BusinessRuleViolationError):
    """La heurística no pudo elegir un insumo único dentro de la familia — error
    interactivo: `options` viaja al frontend para que el operador desambigüe a mano
    y reintente con `override_insumo_id`."""

    default_code = "INSUMO_AMBIGUO"

    def __init__(self, message: str, *, options: list[dict[str, str]]) -> None:
        super().__init__(message, details={"options": options})
        self.options = options


class DatosDeContactoIncompletosError(BusinessRuleViolationError):
    """No se pudieron completar los contactos del pedido con ninguna de las tres capas
    (zona → último pedido de la sucursal → config global)."""

    default_code = "DATOS_DE_CONTACTO_INCOMPLETOS"

    def __init__(self, missing_fields: list[str]) -> None:
        super().__init__(
            "Falta completar datos de contacto (no se encontraron en un pedido reciente "
            "de la sucursal ni en la configuración de la zona/global): "
            + ", ".join(missing_fields),
            details={"missing": missing_fields},
        )


class PedidoNoConfirmadoError(ExternalServiceError):
    """persistNewSupply no devolvió un ID válido — el pedido puede o no existir."""

    default_code = "PEDIDO_NO_CONFIRMADO"

    def __init__(self, device_serial: str) -> None:
        super().__init__(
            f"Canal Directo no confirmó la creación del pedido para la serie "
            f"{device_serial} (persistNewSupply no devolvió un ID válido, revisar "
            "manualmente antes de reintentar)"
        )


class PedidoNoVerificadoError(ExternalServiceError):
    """La verificación post-creación (getSupplyById + NroIncidenteCliente) no confirmó
    que el ID devuelto sea nuestro pedido — NO se marca procesado y NUNCA se reintenta
    automáticamente; el operador decide (ver reconcile para el caso "sí se creó")."""

    default_code = "PEDIDO_NO_VERIFICADO"

    def __init__(self, supply_id: int, device_serial: str) -> None:
        super().__init__(
            f"No se pudo verificar el pedido {supply_id} recién creado para la serie "
            f"{device_serial} (la referencia no coincide o el pedido no aparece — "
            "revisar manualmente antes de reintentar)"
        )


class ConsultaDePedidosNoDisponibleError(ExternalServiceError):
    """Fallaron TODAS las fuentes de pedidos existentes (cache local y getTopSupplies) —
    con fail-closed activo (autocarga) esto pospone la creación en vez de arriesgar
    un duplicado."""

    default_code = "CONSULTA_DE_PEDIDOS_NO_DISPONIBLE"

    def __init__(self, device_serial: str) -> None:
        super().__init__(
            f"No se pudieron consultar pedidos existentes para la serie {device_serial}"
        )


class RespuestaInesperadaDeInsightError(ExternalServiceError):
    """Un endpoint de listado de Insight devolvió un objeto suelto en vez de un array —
    nunca observado en producción, pero mejor fallar claro acá que iterar mal en
    silencio aguas abajo."""

    default_code = "RESPUESTA_INESPERADA_DE_INSIGHT"

    def __init__(self, path: str, payload: object) -> None:
        super().__init__(
            f"Insight API devolvió un objeto en vez de una lista para {path}: {payload!r}"
        )


class OrderAlreadyInProgressError(BusinessRuleViolationError):
    """Ya hay un pedido en curso para esta serie+sku — reemplaza la garantía
    que daba `KeyedLock.acquire((serial, sku))` en la app legacy (un lock en
    memoria de un solo proceso, que no sobrevive a más de un worker/réplica).
    Ver ClaimedOrderCreation."""

    default_code = "ORDER_ALREADY_IN_PROGRESS"

    def __init__(self, device_serial: str, sku: str) -> None:
        super().__init__(
            f"Ya hay un pedido en curso para la serie {device_serial!r} y SKU {sku!r}"
        )
