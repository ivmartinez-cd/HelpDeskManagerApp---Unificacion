/** Helpers de fecha en huso Argentina, para pantallas que muestran o filtran
 * por fecha calendario sin importar el huso del navegador (ver
 * `DateRangePicker` en `shared/components/ui/`). NO usar `new Date().toISOString()`
 * ni `new Date(key)` a secas para `YYYY-MM-DD`: ambos pasan por UTC y corren
 * el día en horario Argentina (UTC-3). */

export const ARG_TZ = "America/Argentina/Buenos_Aires";

/** `Date` → `YYYY-MM-DD` del día calendario argentino. */
export function toArgDateKey(date: Date): string {
  // `en-CA` da directamente el formato ISO de fecha (YYYY-MM-DD).
  return date.toLocaleDateString("en-CA", { timeZone: ARG_TZ });
}

/** `YYYY-MM-DD` de HOY en Argentina. */
export function todayInArg(): string {
  return toArgDateKey(new Date());
}

/** `YYYY-MM-DD` → `11/08/2026`, sin depender del huso del navegador. */
export function formatPlainDate(isoDate: string | null | undefined): string {
  if (!isoDate) return "—";
  const [year, month, day] = isoDate.split("-");
  if (!year || !month || !day) return "—";
  return `${day}/${month}/${year}`;
}
