export interface OperatorShift {
  userId: string;
  userName: string;
  color?: string | null;
  /** Novedad aprobada del día que afecta al operador ('Home office',
   * 'Horario 08:00–17:00', 'Vacaciones'…); null = jornada normal. */
  nota?: string | null;
}

export interface ResolvedShift {
  slotId: string;
  casillaId: string;
  casillaNombre: string;
  casillaColor?: string | null;
  horaInicio: string;
  horaFin: string;
  diaSemana: number;
  operadores: OperatorShift[];
  isCurrent: boolean;
  isNext: boolean;
}

/** Cabecera de la grilla de vacaciones vigente hoy (ADR-025), para el badge
 * de la home. `null` cuando rige la grilla titular. */
export interface VarianteActiva {
  id: string;
  motivo: string | null;
  desde: string;
  hasta: string;
}

export interface CurrentShifts {
  shifts: ResolvedShift[];
  varianteActiva: VarianteActiva | null;
}

export interface Casilla {
  id: string;
  nombre: string;
  color?: string | null;
  sortOrder: number;
  isActive: boolean;
}

export interface Asignacion {
  id: string;
  slotId: string;
  userId: string;
  userName?: string | null;
  vigenteDesde: string;
  vigenteHasta?: string | null;
}

export interface Slot {
  id: string;
  casillaId: string;
  horaInicio: string;
  horaFin: string;
  diaSemana: number;
  sortOrder: number;
  asignaciones: Asignacion[];
}

export interface CreateCasillaPayload {
  nombre: string;
  color?: string | null;
  sortOrder?: number;
  isActive?: boolean;
}

export interface CreateSlotPayload {
  casillaId: string;
  horaInicio: string;
  horaFin: string;
  diaSemana: number;
  sortOrder?: number;
}

// Solo `nombre` es editable en una casilla existente -- color/sortOrder/isActive
// los preserva el backend desde el registro actual (ver UpdateCasillaCommand).
export interface UpdateCasillaPayload {
  nombre: string;
}

// Sin sortOrder -- el backend lo preserva desde el registro actual (ver
// UpdateSlotCommand).
export interface UpdateSlotPayload {
  casillaId: string;
  horaInicio: string;
  horaFin: string;
  diaSemana: number;
}

export interface UserOption {
  id: string;
  fullName: string;
}
