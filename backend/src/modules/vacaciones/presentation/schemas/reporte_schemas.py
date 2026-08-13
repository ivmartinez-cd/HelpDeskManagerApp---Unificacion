from pydantic import BaseModel, ConfigDict, Field

from src.modules.vacaciones.application.dtos.reporte_dtos import (
    FilaEmpleadoReporteDTO,
    FilaSectorReporteDTO,
    ReporteVacacionesDTO,
)


class FilaEmpleadoReporteResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nombre: str
    color: str
    sector_nombre: str = Field(serialization_alias="sectorNombre")
    cargo_nombre: str = Field(serialization_alias="cargoNombre")
    annual: int
    used: int
    pending: int
    available: int

    @classmethod
    def from_dto(cls, dto: FilaEmpleadoReporteDTO) -> "FilaEmpleadoReporteResponse":
        return cls(
            nombre=dto.nombre,
            color=dto.color,
            sector_nombre=dto.sector_nombre,
            cargo_nombre=dto.cargo_nombre,
            annual=dto.annual,
            used=dto.used,
            pending=dto.pending,
            available=dto.available,
        )


class FilaSectorReporteResponse(BaseModel):
    nombre: str
    color: str
    empleados: int
    annual: int
    used: int
    available: int

    @classmethod
    def from_dto(cls, dto: FilaSectorReporteDTO) -> "FilaSectorReporteResponse":
        return cls(
            nombre=dto.nombre,
            color=dto.color,
            empleados=dto.empleados,
            annual=dto.annual,
            used=dto.used,
            available=dto.available,
        )


class ReporteVacacionesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    year: int
    por_empleado: list[FilaEmpleadoReporteResponse] = Field(
        serialization_alias="porEmpleado"
    )
    por_sector: list[FilaSectorReporteResponse] = Field(serialization_alias="porSector")

    @classmethod
    def from_dto(cls, dto: ReporteVacacionesDTO) -> "ReporteVacacionesResponse":
        return cls(
            year=dto.year,
            por_empleado=[FilaEmpleadoReporteResponse.from_dto(f) for f in dto.por_empleado],
            por_sector=[FilaSectorReporteResponse.from_dto(f) for f in dto.por_sector],
        )
