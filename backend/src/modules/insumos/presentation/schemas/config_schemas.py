"""Schemas de GET/PUT /api/insumos/config — contrato camelCase del legacy
(routers/config.py::ConfigResponse y ConfigBody), con los mismos defaults."""

from pydantic import BaseModel, ConfigDict, Field

from src.modules.insumos.application.dtos.insumos_config import (
    ConfigView,
    SaveConfigCommand,
    SaveConfigResult,
)
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings


class ConfigResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    threshold_critical: int = Field(serialization_alias="thresholdCritical")
    threshold_urgent: int = Field(serialization_alias="thresholdUrgent")
    threshold_warning: int = Field(serialization_alias="thresholdWarning")
    autoload_enabled: bool = Field(serialization_alias="autoloadEnabled")
    autoload_max_days: int = Field(serialization_alias="autoloadMaxDays")
    autoload_min_percent: int = Field(serialization_alias="autoloadMinPercent")
    validation_window_hours: int = Field(serialization_alias="validationWindowHours")
    stale_device_days: int = Field(serialization_alias="staleDeviceDays")
    offline_device_hours: int = Field(serialization_alias="offlineDeviceHours")
    offline_monitor_hours: int = Field(serialization_alias="offlineMonitorHours")
    offline_outage_min_devices: int = Field(serialization_alias="offlineOutageMinDevices")
    offline_outage_min_percent: int = Field(serialization_alias="offlineOutageMinPercent")
    alert_escalation_minutes: int = Field(serialization_alias="alertEscalationMinutes")
    alert_work_hours_enabled: bool = Field(serialization_alias="alertWorkHoursEnabled")
    alert_work_hour_start: int = Field(serialization_alias="alertWorkHourStart")
    alert_work_hour_end: int = Field(serialization_alias="alertWorkHourEnd")
    logistics_mail_to: list[str] = Field(serialization_alias="logisticsMailTo")
    ops_alert_mail_to: list[str] = Field(serialization_alias="opsAlertMailTo")

    @classmethod
    def from_view(cls, view: ConfigView) -> "ConfigResponse":
        settings = view.settings
        return cls(
            threshold_critical=settings.threshold_critical,
            threshold_urgent=settings.threshold_urgent,
            threshold_warning=settings.threshold_warning,
            autoload_enabled=settings.autoload_enabled,
            autoload_max_days=settings.autoload_max_days,
            autoload_min_percent=settings.autoload_min_percent,
            validation_window_hours=settings.validation_window_hours,
            stale_device_days=settings.stale_device_days,
            offline_device_hours=settings.offline_device_hours,
            offline_monitor_hours=settings.offline_monitor_hours,
            offline_outage_min_devices=settings.offline_outage_min_devices,
            offline_outage_min_percent=settings.offline_outage_min_percent,
            alert_escalation_minutes=settings.alert_escalation_minutes,
            alert_work_hours_enabled=settings.alert_work_hours_enabled,
            alert_work_hour_start=settings.alert_work_hour_start,
            alert_work_hour_end=settings.alert_work_hour_end,
            logistics_mail_to=view.logistics_mail_to,
            ops_alert_mail_to=view.ops_alert_mail_to,
        )


class ConfigRequestBody(BaseModel):
    """Los defaults son los mismos del legacy: el formulario manda el objeto completo,
    pero un campo ausente cae en el default de negocio y no en 0."""

    model_config = ConfigDict(populate_by_name=True)

    threshold_critical: int = Field(default=3, alias="thresholdCritical")
    threshold_urgent: int = Field(default=7, alias="thresholdUrgent")
    threshold_warning: int = Field(default=14, alias="thresholdWarning")
    autoload_enabled: bool = Field(default=False, alias="autoloadEnabled")
    autoload_max_days: int = Field(default=3, alias="autoloadMaxDays")
    autoload_min_percent: int = Field(default=15, alias="autoloadMinPercent")
    validation_window_hours: int = Field(default=6, alias="validationWindowHours")
    stale_device_days: int = Field(default=5, alias="staleDeviceDays")
    offline_device_hours: int = Field(default=72, alias="offlineDeviceHours")
    offline_monitor_hours: int = Field(default=48, alias="offlineMonitorHours")
    offline_outage_min_devices: int = Field(default=5, alias="offlineOutageMinDevices")
    offline_outage_min_percent: int = Field(default=10, alias="offlineOutageMinPercent")
    alert_escalation_minutes: int = Field(default=60, alias="alertEscalationMinutes")
    alert_work_hours_enabled: bool = Field(default=True, alias="alertWorkHoursEnabled")
    alert_work_hour_start: int = Field(default=8, alias="alertWorkHourStart")
    alert_work_hour_end: int = Field(default=18, alias="alertWorkHourEnd")
    logistics_mail_to: list[str] = Field(default_factory=list, alias="logisticsMailTo")
    ops_alert_mail_to: list[str] = Field(default_factory=list, alias="opsAlertMailTo")

    def to_command(self) -> SaveConfigCommand:
        fields = self.model_dump(exclude={"logistics_mail_to", "ops_alert_mail_to"})
        return SaveConfigCommand(
            settings=InsumosSettings(**fields),
            logistics_mail_to=self.logistics_mail_to,
            ops_alert_mail_to=self.ops_alert_mail_to,
        )


class SaveConfigResponse(BaseModel):
    ok: bool
    error: str | None = None

    @classmethod
    def from_result(cls, result: SaveConfigResult) -> "SaveConfigResponse":
        return cls(ok=result.ok, error=result.error)
