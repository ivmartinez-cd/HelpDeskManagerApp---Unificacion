/** Tipos wire del módulo vacaciones — camelCase vía `serialization_alias` en
 * los schemas Pydantic (verificado contra respuestas reales del backend en el
 * smoke del checkpoint 4/5). */

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export type EstadoEmpleado = "ACTIVE" | "INACTIVE";
export type EstadoSolicitud = "PENDING" | "APPROVED" | "REJECTED";

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

export interface Sector {
  id: string;
  name: string;
  color: string;
  empleadosCount: number;
  jefes: UsuarioOption[];
}

export interface SectorPayload {
  name: string;
  color: string;
  jefeUserId: string | null;
}

export interface Cargo {
  id: string;
  name: string;
  maxSimultaneos: number | null;
  empleadosCount: number;
}

export interface CargoPayload {
  name: string;
  maxSimultaneos: number | null;
}

export interface Feriado {
  id: string;
  name: string;
  date: string; // YYYY-MM-DD
  deductsVacation: boolean;
}

export interface FeriadoPayload {
  name: string;
  date: string;
  deductsVacation: boolean;
}

export interface ImportFeriadosResult {
  year: number;
  count: number;
  message: string;
}

export interface Aprobacion {
  id: string;
  decision: "APPROVED" | "REJECTED";
  comment: string | null;
  createdAt: string;
  approverEmail: string | null;
}

export interface Solicitud {
  id: string;
  empleadoId: string;
  empleadoNombre: string;
  empleadoColor: string;
  sectorNombre: string;
  sectorColor: string;
  startDate: string;
  endDate: string;
  daysRequested: number;
  chargedToYear: number | null;
  reason: string | null;
  status: EstadoSolicitud;
  createdAt: string;
  aprobaciones: Aprobacion[];
}

export interface SolicitudPayload {
  empleadoId?: string;
  startDate: string;
  endDate: string;
  chargedToYear?: number | null;
  reason?: string | null;
}

export interface Saldo {
  annual: number;
  carryOver: number;
  used: number;
  pending: number;
  available: number;
  cycleOpen: boolean;
}

export interface DiasResumen {
  year: number;
  saldo: Saldo | null;
}

export interface EnVacaciones {
  solicitudId: string;
  empleadoNombre: string;
  empleadoColor: string;
  sectorNombre: string;
  sectorColor: string;
  startDate: string;
  endDate: string;
}

export interface DashboardResumen {
  totalEmpleados: number;
  empleadosActivos: number;
  solicitudesPendientes: number;
  enVacaciones: EnVacaciones[];
  dias: DiasResumen | null;
  diasProximo: DiasResumen | null;
  diasTotalesEquipo: number | null;
  diasDisponiblesEquipo: number | null;
}

export interface EventoCalendario {
  id: string;
  title: string;
  start: string;
  end: string; // exclusivo
  tipo: "vacation" | "holiday";
  color: string;
  borderColor: string | null;
  status: EstadoSolicitud | null;
  empleado: string | null;
  sector: string | null;
  dias: number | null;
  restantes: number | null;
  reason: string | null;
}

export interface Solapamientos {
  overlaps: Solicitud[];
  teamSize: number;
}
