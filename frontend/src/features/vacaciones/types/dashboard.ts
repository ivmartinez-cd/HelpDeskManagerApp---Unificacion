import type { Ausencia } from "./ausencias";
import type { Saldo } from "./empleados";
import type { EstadoSolicitud, Solicitud } from "./solicitudes";

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

/** Próximos días del equipo para la card "Equipo" de Inicio (`useProximosEquipo`). */
export interface ProximosEquipo {
  vacaciones: Solicitud[];
  homeOffice: Ausencia[];
  bajas: Ausencia[];
}
