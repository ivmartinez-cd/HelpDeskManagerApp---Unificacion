from src.shared.domain.errors import BusinessRuleViolationError


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
