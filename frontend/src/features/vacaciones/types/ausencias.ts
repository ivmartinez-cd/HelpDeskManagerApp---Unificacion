import type { EstadoSolicitud } from "./solicitudes";

export type TipoAusencia =
  | "DESCUENTO_DIA"
  | "BAJA_ENFERMEDAD"
  | "TRAMITE_PERSONAL"
  | "GUARDIA"
  | "DIA_ESTUDIO"
  | "HOME_OFFICE"
  | "CAMBIO_HORARIO"
  | "OTHER";

/** Lo que un empleado pide desde "Solicitudes" y la TL aprueba (2026-08-21):
 * se modelan como ausencias PENDING (no hay entidad aparte). */
export const TIPOS_SOLICITABLES: TipoAusencia[] = ["HOME_OFFICE", "CAMBIO_HORARIO"];

export interface Ausencia {
  id: string;
  empleadoId: string;
  empleadoNombre: string;
  empleadoColor: string;
  sectorNombre: string;
  sectorColor: string;
  startDate: string;
  endDate: string;
  daysCount: number;
  halfDay: boolean;
  tipo: TipoAusencia;
  reason: string | null;
  status: EstadoSolicitud;
  createdAt: string;
  /** HH:MM:SS, solo CAMBIO_HORARIO */
  horaDesde: string | null;
  horaHasta: string | null;
}

export interface AusenciaPayload {
  empleadoIds?: string[];
  startDate: string;
  endDate: string;
  tipo: TipoAusencia;
  reason: string | null;
  halfDay: boolean;
  status?: EstadoSolicitud;
  /** HH:MM, solo CAMBIO_HORARIO */
  horaDesde?: string | null;
  horaHasta?: string | null;
}

export interface DecisionAusenciaResult {
  id: string;
  status: EstadoSolicitud;
  afectaTurnos: { userId: string; desde: string; hasta: string } | null;
}
