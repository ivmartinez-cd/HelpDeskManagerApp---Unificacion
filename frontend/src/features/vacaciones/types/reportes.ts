export interface DescuentoRow {
  empleadoId: string;
  firstName: string;
  lastName: string;
  cargoNombre: string;
  diasDescontados: number;
  diasEnfermedad: number;
  guardias: number;
}

export interface FilaEmpleadoReporte {
  nombre: string;
  color: string;
  sectorNombre: string;
  cargoNombre: string;
  annual: number;
  used: number;
  pending: number;
  available: number;
}

export interface FilaSectorReporte {
  nombre: string;
  color: string;
  empleados: number;
  annual: number;
  used: number;
  available: number;
}

export interface ReporteVacaciones {
  year: number;
  porEmpleado: FilaEmpleadoReporte[];
  porSector: FilaSectorReporte[];
}
