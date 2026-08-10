from src.shared.domain.errors import BusinessRuleViolationError


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
