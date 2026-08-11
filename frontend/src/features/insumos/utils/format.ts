/** Formateo de fechas y números del módulo Insumos.
 *
 * REGLA: el legacy siempre muestra hora **Argentina**, sin importar el huso del
 * navegador — un operario en otro huso tiene que ver el mismo timestamp que el
 * resto del equipo. Se replica con `Intl` nativo (`timeZone: ARG_TZ`); NO
 * agregar date-fns/dayjs, el proyecto no tiene librería de fechas y no la
 * necesita para esto.
 *
 * Todas las funciones toleran `null`/`undefined`/string vacío y devuelven el
 * placeholder `—`: las respuestas del backend tienen muchísimos campos
 * opcionales y no queremos un `Invalid Date` en la tabla.
 */

export const ARG_TZ = "America/Argentina/Buenos_Aires";
const LOCALE = "es-AR";

/** Lo que se muestra cuando el dato no vino o no es parseable. */
export const EMPTY_VALUE = "—";

function toDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

/** `2026-08-11T14:30:00Z` → `11/08/2026 11:30` (hora Argentina). */
export function formatArgDateTime(value: string | null | undefined): string {
  const date = toDate(value);
  if (!date) return EMPTY_VALUE;
  return date.toLocaleString(LOCALE, {
    timeZone: ARG_TZ,
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

/** `2026-08-11T14:30:00Z` → `11/08/2026` (fecha del día en Argentina). */
export function formatArgDate(value: string | null | undefined): string {
  const date = toDate(value);
  if (!date) return EMPTY_VALUE;
  return date.toLocaleDateString(LOCALE, {
    timeZone: ARG_TZ,
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/** `2026-08-11T14:30:00Z` → `11:30` (hora Argentina). */
export function formatArgTime(value: string | null | undefined): string {
  const date = toDate(value);
  if (!date) return EMPTY_VALUE;
  return date.toLocaleTimeString(LOCALE, {
    timeZone: ARG_TZ,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

/** Etiqueta corta para ejes de gráfico: `2026-08-11` → `11 ago`.
 *
 * Los `YYYY-MM-DD` que devuelve el backend (`format: date`) los parsea JS como
 * medianoche **UTC**, que en Argentina (UTC-3) cae el día anterior. Por eso se
 * fuerza `timeZone: "UTC"` acá y NO ARG_TZ: no es un instante, es un día
 * calendario ya calculado del lado del servidor. */
export function formatDayLabel(isoDate: string | null | undefined): string {
  const date = toDate(isoDate);
  if (!date) return EMPTY_VALUE;
  return date.toLocaleDateString(LOCALE, { timeZone: "UTC", day: "2-digit", month: "short" });
}

/** Igual que `formatDayLabel` pero con el día completo: `11/08/2026`. */
export function formatPlainDate(isoDate: string | null | undefined): string {
  const date = toDate(isoDate);
  if (!date) return EMPTY_VALUE;
  return date.toLocaleDateString(LOCALE, {
    timeZone: "UTC",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/** `YYYY-MM-DD` de HOY en Argentina — la punta que espera el backend en
 * `startDate`/`endDate`. Usar esto y no `new Date().toISOString()`, que da el
 * día UTC (después de las 21:00 local ya adelantó de fecha). */
export function todayInArg(): string {
  return toArgDateKey(new Date());
}

/** Convierte un `Date` al `YYYY-MM-DD` del día calendario **argentino**. */
export function toArgDateKey(date: Date): string {
  // `en-CA` da directamente el formato ISO de fecha (YYYY-MM-DD).
  return date.toLocaleDateString("en-CA", { timeZone: ARG_TZ });
}

/** `4820` → `4.820`. */
export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return EMPTY_VALUE;
  return value.toLocaleString(LOCALE);
}

/** `92.75` → `92,8%`. */
export function formatPercent(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return EMPTY_VALUE;
  return `${value.toLocaleString(LOCALE, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}%`;
}
