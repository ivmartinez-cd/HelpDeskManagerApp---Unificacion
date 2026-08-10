from typing import Protocol


class OrderClaimRepository(Protocol):
    """Puerto de dominio para el mecanismo de idempotencia por (serie, sku).

    `try_claim` es atómico del lado de la implementación real (un `INSERT
    ... ON CONFLICT DO NOTHING` sobre un índice único parcial en Postgres,
    ver SqlAlchemyOrderClaimRepository) — acá no se expone ningún detalle de
    infraestructura, solo el contrato."""

    async def try_claim(self, device_serial: str, sku: str) -> bool:
        """True si se reclamó la clave (nadie más tenía un claim IN_PROGRESS
        para esta serie+sku); False si ya había uno en curso."""
        ...

    async def release(self, device_serial: str, sku: str) -> None:
        """Libera el claim IN_PROGRESS de esta serie+sku. Idempotente: no
        falla si ya no hay ninguno en ese estado."""
        ...
