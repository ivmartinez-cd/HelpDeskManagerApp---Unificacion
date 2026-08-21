export type EstadoEmpleado = "ACTIVE" | "INACTIVE";

export interface Saldo {
  annual: number;
  carryOver: number;
  used: number;
  pending: number;
  available: number;
  cycleOpen: boolean;
}

export interface Empleado {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  hireDate: string; // YYYY-MM-DD
  status: EstadoEmpleado;
  color: string;
  departmentId: string;
  cargoId: string;
  userId: string | null;
}

export interface EmpleadoListItem extends Empleado {
  sectorNombre: string;
  sectorColor: string;
  cargoNombre: string;
  diasAnuales: number;
  antiguedadAnios: number;
  saldo: Saldo;
  saldoSiguiente: Saldo | null;
}

export interface EmpleadoPayload {
  firstName: string;
  lastName: string;
  email: string;
  hireDate: string;
  departmentId: string;
  cargoId: string;
  color: string;
  status: EstadoEmpleado;
  userId: string | null;
}

export interface UsuarioOption {
  id: string;
  email: string;
  fullName: string;
}
