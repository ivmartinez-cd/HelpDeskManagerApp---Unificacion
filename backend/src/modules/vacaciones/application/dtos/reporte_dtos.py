from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FilaEmpleadoReporteDTO:
    nombre: str
    color: str
    sector_nombre: str
    cargo_nombre: str
    annual: int
    used: int
    pending: int
    available: int


@dataclass(frozen=True, slots=True)
class FilaSectorReporteDTO:
    nombre: str
    color: str
    empleados: int
    annual: int
    used: int
    available: int


@dataclass(frozen=True, slots=True)
class ReporteVacacionesDTO:
    year: int
    por_empleado: list[FilaEmpleadoReporteDTO]
    por_sector: list[FilaSectorReporteDTO]
