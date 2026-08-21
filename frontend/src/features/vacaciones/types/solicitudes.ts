export type EstadoSolicitud = "PENDING" | "APPROVED" | "REJECTED";

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

/** Aviso de impacto en turnos al aprobar (ADR-025): el empleado tiene
 * franjas de turno en el rango. No crea nada; alimenta el CTA hacia el
 * editor del modo vacaciones. */
export interface AfectaTurnos {
  userId: string;
  desde: string;
  hasta: string;
}

export interface DecisionResult extends Solicitud {
  afectaTurnos: AfectaTurnos | null;
}

export interface SolicitudPayload {
  empleadoId?: string;
  startDate: string;
  endDate: string;
  chargedToYear?: number | null;
  reason?: string | null;
}

export interface Solapamientos {
  overlaps: Solicitud[];
  teamSize: number;
}
