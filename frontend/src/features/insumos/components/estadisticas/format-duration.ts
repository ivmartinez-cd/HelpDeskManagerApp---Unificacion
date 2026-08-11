import { EMPTY_VALUE } from "../../utils/format";

/** Duraciones de los KPIs del detalle de cliente. Viven acá y no en
 * `utils/format.ts` porque solo las usa esta pantalla: el backend expone
 * minutos (tiempo de atención, en horas hábiles) y días corridos
 * (Pendiente → Despachado). */

/** `135` → `2 h 15 min`; `45` → `45 min`; `null` → `—`. */
export function formatMinutes(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return EMPTY_VALUE;
  const total = Math.max(0, Math.round(value));
  if (total < 60) return `${total} min`;
  const hours = Math.floor(total / 60);
  const minutes = total % 60;
  return minutes === 0 ? `${hours} h` : `${hours} h ${minutes} min`;
}

/** `2.5` → `2,5 días`; `1` → `1 día`; `null` → `—`. */
export function formatDays(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return EMPTY_VALUE;
  const rounded = Math.round(value * 10) / 10;
  const label = rounded.toLocaleString("es-AR", { maximumFractionDigits: 1 });
  return `${label} ${rounded === 1 ? "día" : "días"}`;
}
