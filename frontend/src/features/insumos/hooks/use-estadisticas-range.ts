"use client";

import { useCallback, useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { DateRange, EstadisticasFilters } from "../types";
import { todayInArg } from "../utils/format";

/** Rango de fechas de las pantallas de Estadísticas, sincronizado con el
 * querystring — igual que el legacy, que usa `start_date`/`end_date` en la URL
 * para que el link sea compartible y sobreviva a un F5.
 *
 * Sin parámetros en la URL no se manda `startDate`/`endDate`: se cae al
 * `days` default del backend (30), que además devuelve el rango efectivo en
 * `startDate`/`endDate` de la respuesta. No se escribe ese default en la URL
 * para no ensuciar el historial con un estado que el backend ya sabe resolver.
 *
 * Quien use este hook tiene que estar debajo de un `<Suspense>`
 * (`useSearchParams()` lo exige en el App Router).
 */

export const DEFAULT_DAYS = 30;

/** Opciones del selector de período rápido del `TrendChart` (en días). */
export const QUICK_PERIODS = [
  { key: "7", label: "7 días" },
  { key: "30", label: "30 días" },
  { key: "90", label: "90 días" },
];

const DATE_KEY = /^\d{4}-\d{2}-\d{2}$/;

/** `YYYY-MM-DD` → `Date` local (nunca `new Date(key)`: eso parsea como UTC y
 * en Argentina corre un día para atrás). */
function parseKey(key: string): Date {
  const [year, month, day] = key.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function toKey(date: Date): string {
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

/** Últimos `days` días **inclusive** — misma cuenta que hace el backend con
 * `?days=N` (con 30 devuelve 30 puntos, no 31). */
export function rangeForLastDays(days: number): DateRange {
  const today = parseKey(todayInArg());
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate() - (days - 1));
  return { startDate: toKey(start), endDate: toKey(today) };
}

interface EstadisticasRange {
  /** `null` = sin rango explícito en la URL (el backend usa su default). */
  range: DateRange | null;
  /** Lo que se le pasa tal cual a `getEstadisticas`/`getEstadisticasCliente`. */
  filters: EstadisticasFilters;
  setRange: (next: DateRange | null) => void;
  /** Atajo para las pills de período del gráfico. */
  setLastDays: (days: number) => void;
}

export function useEstadisticasRange(): EstadisticasRange {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const startDate = searchParams.get("start_date");
  const endDate = searchParams.get("end_date");

  const range = useMemo<DateRange | null>(() => {
    // Un querystring editado a mano puede traer cualquier cosa: si no tiene la
    // forma que espera el backend se ignora, en vez de mandar un 422.
    if (!startDate || !endDate) return null;
    if (!DATE_KEY.test(startDate) || !DATE_KEY.test(endDate)) return null;
    return startDate <= endDate
      ? { startDate, endDate }
      : { startDate: endDate, endDate: startDate };
  }, [startDate, endDate]);

  const filters = useMemo<EstadisticasFilters>(
    () => (range ? { startDate: range.startDate, endDate: range.endDate } : { days: DEFAULT_DAYS }),
    [range],
  );

  const setRange = useCallback(
    (next: DateRange | null) => {
      const params = new URLSearchParams(searchParams.toString());
      if (next) {
        params.set("start_date", next.startDate);
        params.set("end_date", next.endDate);
      } else {
        params.delete("start_date");
        params.delete("end_date");
      }
      const query = params.toString();
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  const setLastDays = useCallback((days: number) => setRange(rangeForLastDays(days)), [setRange]);

  return { range, filters, setRange, setLastDays };
}

/** Serializa el rango vigente para propagarlo a otra pantalla (el link del
 * ranking de clientes al detalle) sin perder el período elegido. */
export function rangeToQuery(range: DateRange | null): string {
  if (!range) return "";
  return `?start_date=${range.startDate}&end_date=${range.endDate}`;
}
