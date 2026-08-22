import type { DateRange } from "../../types/common";
import { todayInArg } from "../../utils/format";

/** Helpers puros del selector de rango (`date-range-picker.tsx`): presets,
 * conversión `YYYY-MM-DD` ⇄ `Date` local y celdas del mes. */

export const WEEKDAYS = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"];

export const PRESET_KEYS = ["hoy", "semana", "mes", "mespasado", "trimestre", "custom"] as const;
export type DateRangePresetKey = (typeof PRESET_KEYS)[number];

export const PRESET_LABELS: Record<DateRangePresetKey, string> = {
  hoy: "Hoy",
  semana: "Esta semana",
  mes: "Este mes",
  mespasado: "Mes pasado",
  trimestre: "Último trimestre",
  custom: "Personalizado",
};

/** `YYYY-MM-DD` → `Date` a medianoche LOCAL. Nunca usar `new Date(key)` a
 * secas: eso parsea el string como UTC y corre un día para atrás en -03. */
export function parseKey(key: string): Date {
  const [year, month, day] = key.split("-").map(Number);
  return new Date(year, month - 1, day);
}

/** `Date` local → `YYYY-MM-DD`, sin pasar por `toISOString()` (que convierte a
 * UTC y vuelve a correr el día). */
export function toKey(date: Date): string {
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

/** Rango de cada preset, calculado sobre el día de hoy en Argentina.
 * `custom` devuelve `null`: solo cambia el modo, no toca las fechas. */
export function rangeForPreset(preset: DateRangePresetKey): DateRange | null {
  const today = parseKey(todayInArg());
  const y = today.getFullYear();
  const m = today.getMonth();
  switch (preset) {
    case "hoy":
      return { startDate: toKey(today), endDate: toKey(today) };
    case "semana": {
      // Semana que arranca el lunes (getDay(): 0 = domingo).
      const offset = (today.getDay() + 6) % 7;
      const monday = new Date(y, m, today.getDate() - offset);
      return { startDate: toKey(monday), endDate: toKey(today) };
    }
    case "mes":
      return { startDate: toKey(new Date(y, m, 1)), endDate: toKey(today) };
    case "mespasado":
      return { startDate: toKey(new Date(y, m - 1, 1)), endDate: toKey(new Date(y, m, 0)) };
    case "trimestre":
      return { startDate: toKey(new Date(y, m - 3, today.getDate())), endDate: toKey(today) };
    default:
      return null;
  }
}

/** Celdas del mes: los huecos iniciales van como `null`. */
export function buildMonthCells(year: number, month: number): (Date | null)[] {
  const first = new Date(year, month, 1);
  const leading = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: (Date | null)[] = Array.from({ length: leading }, () => null);
  for (let day = 1; day <= daysInMonth; day++) cells.push(new Date(year, month, day));
  return cells;
}
