"""Schemas del endpoint /load — mismo contrato camelCase que el frontend legacy."""

from pydantic import BaseModel, ConfigDict, Field

from src.modules.insumos.application.dtos.load_order import LoadOrderResult


class LoadRequestBody(BaseModel):
    """Deliberadamente NO acepta deviceId/serial/sku: todo se deriva del lado del
    servidor releyendo Insight (diseño de seguridad del legacy)."""

    model_config = ConfigDict(populate_by_name=True)

    customer_id: int = Field(validation_alias="customerId")
    customer_name: str = Field(validation_alias="customerName")
    dry_run: bool = Field(default=False, validation_alias="dryRun")
    force_override: bool = Field(default=False, validation_alias="forceOverride")
    override_insumo_id: str | None = Field(default=None, validation_alias="overrideInsumoId")
    revision: bool = True


class LoadResponse(BaseModel):
    """Status 200 SIEMPRE: éxito y errores de negocio viajan en el body."""

    ok: bool
    order_id: str | None = Field(default=None, serialization_alias="orderId")
    supply_url: str | None = Field(default=None, serialization_alias="supplyUrl")
    warn: str | None = None
    error: str | None = None
    conflict_type: str | None = Field(default=None, serialization_alias="conflictType")
    conflict_data: dict[str, object] | None = Field(
        default=None, serialization_alias="conflictData"
    )
    options: list[dict[str, str]] | None = None

    @classmethod
    def from_result(cls, result: LoadOrderResult) -> "LoadResponse":
        return cls(
            ok=result.ok,
            order_id=result.order_id,
            supply_url=result.supply_url,
            warn=result.warn,
            error=result.error,
            conflict_type=result.conflict_type,
            conflict_data=result.conflict_data or None,
            options=result.insumo_options or None,
        )
