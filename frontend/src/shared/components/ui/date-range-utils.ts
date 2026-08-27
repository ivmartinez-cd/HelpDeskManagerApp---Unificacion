import type { DateRange } from "@/shared/types/date-range";
import { todayInArg } from "@/shared/utils/date-arg";

/** Helpers puros del selector de rango (`date-range-picker.tsx`): presets por
 * default, conversión `YYYY-MM-DD` ⇄ `Date` local y celdas del mes. */

export const WEEKDAYS = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"];

export interface DateRangePreset {
  key: string;
  label: string;
  /** `null` → no calcula rango, solo resalta el botón (ej. "Personalizado":
   * el usuario ya puede elegir fechas directo en la grilla sin este preset,
   * es puramente indicativo). */
  range: (() => DateRange) | null;
}

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

/** Presets del selector cuando el consumidor no pasa los suyos propios
 * (`DateRangePicker` los usa por default) — calculados sobre el día de hoy
 * en Argentina. */
export const DEFAULT_PRESETS: DateRangePreset[] = [
  {
    key: "hoy",
    label: "Hoy",
    range: () => {
      const today = parseKey(todayInArg());
      return { startDate: toKey(today), endDate: toKey(today) };
    },
  },
  {
    key: "semana",
    label: "Esta semana",
    range: () => {
      const today = parseKey(todayInArg());
      // Semana que arranca el lunes (getDay(): 0 = domingo).
      const offset = (today.getDay() + 6) % 7;
      const monday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - offset);
      return { startDate: toKey(monday), endDate: toKey(today) };
    },
  },
  {
    key: "mes",
    label: "Este mes",
    range: () => {
      const today = parseKey(todayInArg());
      return {
        startDate: toKey(new Date(today.getFullYear(), today.getMonth(), 1)),
        endDate: toKey(today),
      };
    },
  },
  {
    key: "mespasado",
    label: "Mes pasado",
    range: () => {
      const today = parseKey(todayInArg());
      const y = today.getFullYear();
      const m = today.getMonth();
      return {
        startDate: toKey(new Date(y, m - 1, 1)),
        endDate: toKey(new Date(y, m, 0)),
      };
    },
  },
  {
    key: "trimestre",
    label: "Último trimestre",
    range: () => {
      const today = parseKey(todayInArg());
      return {
        startDate: toKey(new Date(today.getFullYear(), today.getMonth() - 3, today.getDate())),
        endDate: toKey(today),
      };
    },
  },
  { key: "custom", label: "Personalizado", range: null },
];

/** Celdas del mes: los huecos iniciales van como `null`. */
export function buildMonthCells(year: number, month: number): (Date | null)[] {
  const first = new Date(year, month, 1);
  const leading = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: (Date | null)[] = Array.from({ length: leading }, () => null);
  for (let day = 1; day <= daysInMonth; day++) cells.push(new Date(year, month, day));
  return cells;
}
