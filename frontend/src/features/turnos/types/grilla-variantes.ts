/** Tipos wire del modo vacaciones (grilla variante, ADR-025). camelCase vía
 * `serialization_alias` en `grilla_variante_schemas.py`. */

import type { OperatorShift } from "./turnos";

/** Estado persistido en DB: solo ACTIVA/CANCELADA. Programada/Vigente/Vencida
 * se derivan por fecha en `lib/variante-estado.ts` (mismo criterio que
 * Coberturas, ADR-013). */
export type VarianteEstadoDb = "ACTIVA" | "CANCELADA";

export type VarianteEstadoUi = "vigente" | "programada" | "vencida" | "cancelada";

export type TipoAdvertencia = "HUECO" | "SIN_OPERADOR" | "OPERADOR_AUSENTE";

export interface AdvertenciaCobertura {
  tipo: TipoAdvertencia;
  casillaId: string | null;
  casillaNombre: string | null;
  diaSemana: number | null;
  /** HH:MM:SS */
  horaInicio: string | null;
  horaFin: string | null;
  userId: string | null;
  userName: string | null;
  desde: string | null;
  hasta: string | null;
  /** OPERADOR_AUSENTE: qué lo ausenta ('Vacaciones', 'Horario 08:00–17:00'…). */
  detalle?: string | null;
}

export interface VarianteSlot {
  id: string;
  casillaId: string;
  casillaNombre: string;
  diaSemana: number;
  horaInicio: string;
  horaFin: string;
  sortOrder: number;
  operadores: OperatorShift[];
}

export interface GrillaVariante {
  id: string;
  motivo: string | null;
  origenTexto: string | null;
  /** ISO YYYY-MM-DD (fecha pura) */
  desde: string;
  hasta: string;
  estado: VarianteEstadoDb;
  createdByUserId: string;
  slots: VarianteSlot[];
  advertencias: AdvertenciaCobertura[];
}

export interface VarianteSlotPayload {
  casillaId: string;
  diaSemana: number;
  /** HH:MM */
  horaInicio: string;
  horaFin: string;
  userIds: string[];
}

export interface GrillaVariantePayload {
  motivo: string | null;
  origenTexto: string | null;
  desde: string;
  hasta: string;
  slots: VarianteSlotPayload[];
}

export interface PrecargaSlot {
  casillaId: string;
  casillaNombre: string;
  diaSemana: number;
  horaInicio: string;
  horaFin: string;
  sortOrder: number;
  /** Ya sin el ausente */
  operadores: OperatorShift[];
  /** La franja era del ausente: hueco a resolver */
  requiereCobertura: boolean;
}

export interface PrecargaGrilla {
  ausenteUserId: string;
  ausenteNombre: string | null;
  desde: string;
  hasta: string;
  slots: PrecargaSlot[];
  /** Solo OPERADOR_AUSENTE: otros titulares con vacaciones aprobadas en el rango */
  advertencias: AdvertenciaCobertura[];
}

/** Franja en edición (estado local del editor). `key` es solo de UI. */
export interface FranjaEditable {
  key: string;
  casillaId: string;
  diaSemana: number;
  horaInicio: string;
  horaFin: string;
  userIds: string[];
  requiereCobertura: boolean;
}
