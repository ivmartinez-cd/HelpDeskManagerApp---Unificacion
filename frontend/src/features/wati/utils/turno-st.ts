import type { ResolvedShift } from "@/features/turnos/types/turnos";

/** Nombre de la casilla de turnos que representa Servicio Técnico (sembrada
 * por la migración `f7a93b218401_turnos_schema`). */
export const CASILLA_ST = "ST";

function horaLocal(now: Date): string {
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}:00`;
}

/** Franjas de la casilla ST que están corriendo ahora mismo. Se recalcula
 * con la hora local del navegador (no con `isCurrent`, que quedó fijado en
 * el momento del fetch) para que el cambio de turno no dependa del
 * intervalo de refresco. */
export function franjasStVigentes(shifts: ResolvedShift[], now: Date): ResolvedShift[] {
  const ahora = horaLocal(now);
  return shifts.filter(
    (s) => s.casillaNombre.trim().toUpperCase() === CASILLA_ST && s.horaInicio <= ahora && ahora < s.horaFin,
  );
}

export function enHorarioSt(shifts: ResolvedShift[], now: Date): boolean {
  return franjasStVigentes(shifts, now).length > 0;
}

/** ¿El usuario logueado es uno de los operadores asignados a la franja ST en
 * curso? Los turnos ya vienen resueltos con vacaciones e intercambios
 * (ADR-025/026), así que quien figura acá es quien de verdad está cubriendo. */
export function esOperadorStEnTurno(shifts: ResolvedShift[], userId: string, now: Date): boolean {
  return franjasStVigentes(shifts, now).some((s) => s.operadores.some((o) => o.userId === userId));
}
