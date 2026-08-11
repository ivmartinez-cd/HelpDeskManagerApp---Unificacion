"""Schemas de equipos sin registrar — contrato camelCase del legacy
(routers/new_devices.py::NewDeviceRow), con fechas ISO en vez de strings de SQLite."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.insumos.application.dtos.new_devices import NewDeviceRow
from src.modules.insumos.application.use_cases.sync_new_devices import SyncNewDevicesResult


class NewDeviceRowOut(BaseModel):
    device_id: int = Field(serialization_alias="deviceId")
    customer_id: int = Field(serialization_alias="customerId")
    customer_name: str = Field(serialization_alias="customerName")
    serial: str
    model: str
    zone: str
    ip_address: str = Field(serialization_alias="ipAddress")
    monitor_status: str = Field(serialization_alias="monitorStatus")
    discovery_date: datetime | None = Field(
        default=None, serialization_alias="discoveryDate"
    )
    last_contact: datetime | None = Field(default=None, serialization_alias="lastContact")
    first_seen_at: datetime = Field(serialization_alias="firstSeenAt")
    dismissed: bool
    registration_url: str = Field(serialization_alias="registrationUrl")

    @classmethod
    def from_row(cls, row: NewDeviceRow) -> "NewDeviceRowOut":
        device = row.device
        return cls(
            device_id=device.device_id,
            customer_id=device.customer_id,
            customer_name=device.customer_name,
            serial=device.serial,
            model=device.model,
            zone=device.zone,
            ip_address=device.ip_address,
            monitor_status=device.monitor_status,
            discovery_date=device.discovery_date,
            last_contact=device.last_contact,
            first_seen_at=device.first_seen_at,
            dismissed=device.dismissed,
            registration_url=row.registration_url,
        )


class NewDevicesSummaryOut(BaseModel):
    pending_count: int = Field(serialization_alias="pendingCount")


class DismissRequestBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dismissed: bool


class DismissDeviceResponse(BaseModel):
    ok: bool


class SyncNewDevicesResponse(BaseModel):
    """Resultado del sync, no el listado: la lista actualizada se pide con el GET
    (paginado) — el legacy devolvía las dos cosas en la misma respuesta."""

    new_devices: int = Field(serialization_alias="newDevices")
    pruned: int

    @classmethod
    def from_result(cls, result: SyncNewDevicesResult) -> "SyncNewDevicesResponse":
        return cls(new_devices=len(result.new_device_ids), pruned=result.pruned)
