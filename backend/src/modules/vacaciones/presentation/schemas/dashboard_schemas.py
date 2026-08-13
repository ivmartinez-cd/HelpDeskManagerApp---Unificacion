import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from src.modules.vacaciones.application.dtos.dashboard_dtos import (
    AbrirCiclosResultDTO,
    CicloDTO,
    DashboardResumenDTO,
    DiasDTO,
    EnVacacionesDTO,
    EventoCalendarioDTO,
)
from src.modules.vacaciones.domain.value_objects.saldo import Saldo


class SaldoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    annual: int
    carry_over: int = Field(serialization_alias="carryOver")
    used: int
    pending: int
    available: int
    cycle_open: bool = Field(serialization_alias="cycleOpen")

    @classmethod
    def from_saldo(cls, saldo: Saldo) -> "SaldoResponse":
        return cls(
            annual=saldo.annual,
            carry_over=saldo.carry_over,
            used=saldo.used,
            pending=saldo.pending,
            available=saldo.available,
            cycle_open=saldo.cycle_open,
        )


class DiasResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    year: int
    saldo: SaldoResponse | None

    @classmethod
    def from_dto(cls, dto: DiasDTO) -> "DiasResponse":
        return cls(
            year=dto.year,
            saldo=SaldoResponse.from_saldo(dto.saldo) if dto.saldo else None,
        )


class EnVacacionesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    solicitud_id: uuid.UUID = Field(serialization_alias="solicitudId")
    empleado_nombre: str = Field(serialization_alias="empleadoNombre")
    empleado_color: str = Field(serialization_alias="empleadoColor")
    sector_nombre: str = Field(serialization_alias="sectorNombre")
    sector_color: str = Field(serialization_alias="sectorColor")
    start_date: date = Field(serialization_alias="startDate")
    end_date: date = Field(serialization_alias="endDate")

    @classmethod
    def from_dto(cls, dto: EnVacacionesDTO) -> "EnVacacionesResponse":
        return cls(
            solicitud_id=dto.solicitud_id,
            empleado_nombre=dto.empleado_nombre,
            empleado_color=dto.empleado_color,
            sector_nombre=dto.sector_nombre,
            sector_color=dto.sector_color,
            start_date=dto.start_date,
            end_date=dto.end_date,
        )


class DashboardResumenResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_empleados: int = Field(serialization_alias="totalEmpleados")
    empleados_activos: int = Field(serialization_alias="empleadosActivos")
    solicitudes_pendientes: int = Field(serialization_alias="solicitudesPendientes")
    en_vacaciones: list[EnVacacionesResponse] = Field(serialization_alias="enVacaciones")
    dias: DiasResponse | None
    dias_proximo: DiasResponse | None = Field(serialization_alias="diasProximo")
    dias_totales_equipo: int | None = Field(serialization_alias="diasTotalesEquipo")
    dias_disponibles_equipo: int | None = Field(serialization_alias="diasDisponiblesEquipo")

    @classmethod
    def from_dto(cls, dto: DashboardResumenDTO) -> "DashboardResumenResponse":
        return cls(
            total_empleados=dto.total_empleados,
            empleados_activos=dto.empleados_activos,
            solicitudes_pendientes=dto.solicitudes_pendientes,
            en_vacaciones=[EnVacacionesResponse.from_dto(e) for e in dto.en_vacaciones],
            dias=DiasResponse.from_dto(dto.dias) if dto.dias else None,
            dias_proximo=(
                DiasResponse.from_dto(dto.dias_proximo) if dto.dias_proximo else None
            ),
            dias_totales_equipo=dto.dias_totales_equipo,
            dias_disponibles_equipo=dto.dias_disponibles_equipo,
        )


class EventoCalendarioResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    start: date
    end: date  # exclusivo (convención del legacy/FullCalendar)
    tipo: str
    color: str
    border_color: str | None = Field(serialization_alias="borderColor")
    status: str | None
    empleado: str | None
    sector: str | None
    dias: int | None
    restantes: int | None
    reason: str | None

    @classmethod
    def from_dto(cls, dto: EventoCalendarioDTO) -> "EventoCalendarioResponse":
        return cls(
            id=dto.id,
            title=dto.titulo,
            start=dto.start,
            end=dto.end_exclusivo,
            tipo=dto.tipo,
            color=dto.color,
            border_color=dto.border_color,
            status=dto.status,
            empleado=dto.empleado,
            sector=dto.sector,
            dias=dto.dias,
            restantes=dto.restantes,
            reason=dto.reason,
        )


class CicloResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    empleado_id: uuid.UUID = Field(serialization_alias="empleadoId")
    empleado_nombre: str = Field(serialization_alias="empleadoNombre")
    year: int
    annual_days: int = Field(serialization_alias="annualDays")
    carry_over: int = Field(serialization_alias="carryOver")
    is_open: bool = Field(serialization_alias="isOpen")

    @classmethod
    def from_dto(cls, dto: CicloDTO) -> "CicloResponse":
        return cls(
            id=dto.ciclo.id,
            empleado_id=dto.ciclo.empleado_id,
            empleado_nombre=dto.empleado_nombre,
            year=dto.ciclo.year,
            annual_days=dto.ciclo.annual_days,
            carry_over=dto.ciclo.carry_over,
            is_open=dto.ciclo.is_open,
        )


class AbrirCiclosResponse(BaseModel):
    opened: int
    skipped: int

    @classmethod
    def from_dto(cls, dto: AbrirCiclosResultDTO) -> "AbrirCiclosResponse":
        return cls(opened=dto.opened, skipped=dto.skipped)
