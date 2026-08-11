"""Schemas de acciones sobre equipos offline (verify, delete, dismiss)."""

from pydantic import BaseModel, ConfigDict, Field

from src.modules.insumos.application.use_cases.delete_offline_devices import (
    DeleteOfflineDevicesResult,
    DeleteResult,
)
from src.modules.insumos.application.use_cases.verify_offline_devices import VerifySummary


class VerifyBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    limit: int = Field(ge=1, le=50)
    customer_id: int | None = Field(default=None, alias="customerId")


class VerifyResponse(BaseModel):
    checked: int
    bodega: int
    otro_cliente: int = Field(serialization_alias="otroCliente")
    en_cliente: int = Field(serialization_alias="enCliente")
    errores: int
    remaining: int

    @classmethod
    def from_summary(cls, summary: VerifySummary) -> "VerifyResponse":
        return cls(
            checked=summary.checked,
            bodega=summary.bodega,
            otro_cliente=summary.otro_cliente,
            en_cliente=summary.en_cliente,
            errores=summary.errores,
            remaining=summary.remaining,
        )


class OfflineDismissBody(BaseModel):
    dismissed: bool


class OfflineDismissResponse(BaseModel):
    ok: bool


class DeleteResultOut(BaseModel):
    device_id: int = Field(serialization_alias="deviceId")
    serial: str
    ok: bool
    error: str | None = None

    @classmethod
    def from_result(cls, r: DeleteResult) -> "DeleteResultOut":
        return cls(device_id=r.device_id, serial=r.serial, ok=r.ok, error=r.error)


class DeleteBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    device_ids: list[int] = Field(alias="deviceIds")


class DeleteResponse(BaseModel):
    results: list[DeleteResultOut]
    dry_run: bool = Field(serialization_alias="dryRun")

    @classmethod
    def from_result(cls, result: DeleteOfflineDevicesResult) -> "DeleteResponse":
        return cls(
            results=[DeleteResultOut.from_result(r) for r in result.results],
            dry_run=result.dry_run,
        )
