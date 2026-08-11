"""Schemas de lectura de equipos offline y caídas de colector."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.modules.insumos.domain.value_objects.offline_device import MassOutage, OfflineDevice


class OfflineDeviceOut(BaseModel):
    device_id: int = Field(serialization_alias="deviceId")
    customer_id: int = Field(serialization_alias="customerId")
    customer_name: str = Field(serialization_alias="customerName")
    serial: str
    model: str
    zone: str
    last_contact: datetime | None = Field(default=None, serialization_alias="lastContact")
    days_offline: int | None = Field(default=None, serialization_alias="daysOffline")
    cd_status: str = Field(serialization_alias="cdStatus")
    cd_detail: str = Field(serialization_alias="cdDetail")
    cd_checked_at: datetime | None = Field(default=None, serialization_alias="cdCheckedAt")
    offline_dismissed: bool = Field(serialization_alias="offlineDismissed")
    in_mass_outage: bool = Field(serialization_alias="inMassOutage")
    deletable: bool

    @classmethod
    def from_device(
        cls,
        device: OfflineDevice,
        *,
        in_mass_outage: bool,
        deletable: bool,
        days_offline: int | None,
    ) -> "OfflineDeviceOut":
        return cls(
            device_id=device.device_id,
            customer_id=device.customer_id,
            customer_name=device.customer_name,
            serial=device.serial,
            model=device.model,
            zone=device.zone,
            last_contact=device.last_contact,
            days_offline=days_offline,
            cd_status=device.cd_status,
            cd_detail=device.cd_detail,
            cd_checked_at=device.cd_checked_at,
            offline_dismissed=device.offline_dismissed,
            in_mass_outage=in_mass_outage,
            deletable=deletable,
        )


class MassOutageOut(BaseModel):
    customer_id: int = Field(serialization_alias="customerId")
    customer_name: str = Field(serialization_alias="customerName")
    day: str
    device_count: int = Field(serialization_alias="deviceCount")
    fleet_size: int = Field(serialization_alias="fleetSize")
    confirmed: bool
    monitor_name: str = Field(serialization_alias="monitorName")
    monitor_online: bool = Field(serialization_alias="monitorOnline")

    @classmethod
    def from_outage(cls, outage: MassOutage) -> "MassOutageOut":
        return cls(
            customer_id=outage.customer_id,
            customer_name=outage.customer_name,
            day=outage.day,
            device_count=len(outage.device_ids),
            fleet_size=outage.fleet_size,
            confirmed=outage.confirmed,
            monitor_name=outage.monitor_name,
            monitor_online=outage.monitor_online,
        )


class OfflineSummaryOut(BaseModel):
    candidate_count: int = Field(serialization_alias="candidateCount")
