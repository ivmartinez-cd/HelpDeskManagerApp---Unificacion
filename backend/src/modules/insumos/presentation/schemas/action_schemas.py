"""Schemas de /cancel, /dismiss, /ignore y /reconcile — mismo contrato camelCase del
legacy."""

from pydantic import BaseModel, ConfigDict, Field

from src.modules.insumos.application.dtos.request_actions import (
    CancelResult,
    DismissResult,
    IgnoreResult,
    ReconcileResult,
)


class CancelResponse(BaseModel):
    ok: bool
    supply_status: str | None = Field(default=None, serialization_alias="supplyStatus")
    error: str | None = None

    @classmethod
    def from_result(cls, result: CancelResult) -> "CancelResponse":
        return cls(ok=result.ok, supply_status=result.supply_status, error=result.error)


class DismissRequestBody(BaseModel):
    """customer/serial/sku son metadatos para el Historial — la baja en HP SDS usa el id
    del path. supply_id/supply_status vienen de la fila cuando tiene el badge de "pedido
    activo sin confirmar entrega" — determinan si el descarte usa IGNORE en vez de
    DELETE (ver DismissRequest)."""

    model_config = ConfigDict(populate_by_name=True)

    customer_id: int | None = Field(default=None, validation_alias="customerId")
    customer_name: str = Field(default="", validation_alias="customerName")
    serial: str = ""
    sku: str = ""
    supply_id: str | None = Field(default=None, validation_alias="supplyId")
    supply_status: str | None = Field(default=None, validation_alias="supplyStatus")


class DismissResponse(BaseModel):
    ok: bool
    error: str | None = None

    @classmethod
    def from_result(cls, result: DismissResult) -> "DismissResponse":
        return cls(ok=result.ok, error=result.error)


class IgnoreRequestBody(BaseModel):
    """Mismo shape que DismissRequestBody — supply_id acá es opcional de verdad: una
    solicitud sin pedido asociado también puede ignorarse permanentemente."""

    model_config = ConfigDict(populate_by_name=True)

    customer_id: int | None = Field(default=None, validation_alias="customerId")
    customer_name: str = Field(default="", validation_alias="customerName")
    serial: str = ""
    sku: str = ""
    supply_id: str | None = Field(default=None, validation_alias="supplyId")
    supply_status: str | None = Field(default=None, validation_alias="supplyStatus")


class IgnoreResponse(BaseModel):
    ok: bool
    error: str | None = None

    @classmethod
    def from_result(cls, result: IgnoreResult) -> "IgnoreResponse":
        return cls(ok=result.ok, error=result.error)


class ReconcileRequestBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    customer_id: int = Field(validation_alias="customerId")
    customer_name: str = Field(default="", validation_alias="customerName")


class ReconcileResponse(BaseModel):
    ok: bool
    order_id: str | None = Field(default=None, serialization_alias="orderId")
    supply_url: str | None = Field(default=None, serialization_alias="supplyUrl")
    already_linked: bool = Field(default=False, serialization_alias="alreadyLinked")
    error: str | None = None

    @classmethod
    def from_result(cls, result: ReconcileResult) -> "ReconcileResponse":
        return cls(
            ok=result.ok,
            order_id=result.order_id,
            supply_url=result.supply_url,
            already_linked=result.already_linked,
            error=result.error,
        )
