"""Schemas de los reads de detalle de equipo/consumible — mismo contrato camelCase que
el legacy (routers/requests/models.py: DeviceSuppliesResponse, ConsumableHistoryResponse,
ConsumableRequestHistoryResponse, AvailabilityWindowsResponse, ConsumableDetail)."""

from pydantic import BaseModel, Field

from src.modules.insumos.application.dtos.device_detail import (
    ConsumableDetailResult,
    ConsumableHistoryPoint,
    ConsumableRequestHistoryRow,
    DeviceSupplyRow,
)
from src.modules.insumos.domain.services.availability_windows import AvailabilityWindow


class DeviceSupplyItemOut(BaseModel):
    supply_id: int
    supply_id_full: str
    serial: str
    estado: str
    fecha: str
    sku: str
    descripcion: str
    supply_url: str | None = Field(default=None, serialization_alias="supplyUrl")
    source: str  # "soap" | "local"

    @classmethod
    def from_row(cls, row: DeviceSupplyRow) -> "DeviceSupplyItemOut":
        return cls(**{name: getattr(row, name) for name in cls.model_fields})


class DeviceSuppliesResponse(BaseModel):
    """Top-N acotado (limit ≤ 20) para el modal de detalle, no una tabla paginable —
    mismo criterio que el dashboard (colecciones inline en un objeto de vista)."""

    serial: str
    supplies: list[DeviceSupplyItemOut]
    dry_run: bool = Field(serialization_alias="dryRun")


class ConsumableHistoryPointOut(BaseModel):
    date: str
    level: int | None = None

    @classmethod
    def from_point(cls, point: ConsumableHistoryPoint) -> "ConsumableHistoryPointOut":
        return cls(date=point.date, level=point.level)


class ConsumableHistoryResponse(BaseModel):
    """Serie completa del gráfico de nivel (~12 meses) — un gráfico partido en páginas
    no tiene sentido; el rango ya lo acota Insight."""

    points: list[ConsumableHistoryPointOut]


class ConsumableRequestHistoryItemOut(BaseModel):
    request_id: int = Field(serialization_alias="requestId")
    requested: str
    status: str
    status_label: str = Field(serialization_alias="statusLabel")
    reason: str | None = None
    requested_level: int | None = Field(default=None, serialization_alias="requestedLevel")
    requested_days_left: int | None = Field(
        default=None, serialization_alias="requestedDaysLeft"
    )

    @classmethod
    def from_row(cls, row: ConsumableRequestHistoryRow) -> "ConsumableRequestHistoryItemOut":
        return cls(**{name: getattr(row, name) for name in cls.model_fields})


class ConsumableRequestHistoryResponse(BaseModel):
    """Historial acotado por el rango de 12 meses de Insight, para la tabla del modal."""

    items: list[ConsumableRequestHistoryItemOut]


class AvailabilityWindowOut(BaseModel):
    start: str
    end: str

    @classmethod
    def from_window(cls, window: AvailabilityWindow) -> "AvailabilityWindowOut":
        return cls(start=window.start, end=window.end)


class AvailabilityWindowsResponse(BaseModel):
    windows: list[AvailabilityWindowOut]


class ConsumableDetailOut(BaseModel):
    model: str | None = None
    type: str | None = None
    colour: str | None = None
    serial_number: str | None = Field(default=None, serialization_alias="serialNumber")
    sku: str | None = None
    adjusted_yield: int | None = Field(default=None, serialization_alias="adjustedYield")
    reorder_sku: str | None = Field(default=None, serialization_alias="reorderSku")
    reorder_yield: int | None = Field(default=None, serialization_alias="reorderYield")
    capacity: int | None = None
    percent_left: int | None = Field(default=None, serialization_alias="percentLeft")
    days_left: int | None = Field(default=None, serialization_alias="daysLeft")
    pages_left: int | None = Field(default=None, serialization_alias="pagesLeft")
    last_read: str | None = Field(default=None, serialization_alias="lastRead")
    engine_cycles: int | None = Field(default=None, serialization_alias="engineCycles")
    first_read: str | None = Field(default=None, serialization_alias="firstRead")
    days_monitored: int | None = Field(default=None, serialization_alias="daysMonitored")
    engine_cycles_monitored: int | None = Field(
        default=None, serialization_alias="engineCyclesMonitored"
    )

    @classmethod
    def from_result(cls, result: ConsumableDetailResult) -> "ConsumableDetailOut":
        return cls(**{name: getattr(result, name) for name in cls.model_fields})
