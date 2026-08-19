import { toneForStatusKey, type StatusTone } from "../shared";
import { toArgDateKey } from "../../utils/format";
import type { SortValue } from "../../hooks/use-table-sort";
import type { NewDeviceRow } from "../../types";

/** Columnas ordenables de la tabla de Equipos Nuevos. La columna de acciones
 * queda afuera a propósito. */
export const NEW_DEVICE_SORT_KEYS = [
  "customerName",
  "model",
  "serial",
  "zone",
  "ipAddress",
  "monitorStatus",
  "discoveryDate",
  "lastContact",
] as const;

export type NewDeviceSortKey = (typeof NEW_DEVICE_SORT_KEYS)[number];

/** Las fechas arrancan descendentes: lo recién descubierto es lo accionable. */
export const NEW_DEVICE_DESC_FIRST: readonly NewDeviceSortKey[] = ["discoveryDate", "lastContact"];

export const NEW_DEVICES_SORT_STORAGE_KEY = "insumos.equipos-nuevos.sort";

/** Valor comparable de cada columna. Las fechas se comparan como timestamp
 * (nunca como texto: `31/01` sería mayor que `01/02` alfabéticamente). */
export function newDeviceSortValue(row: NewDeviceRow, key: NewDeviceSortKey): SortValue {
  if (key === "discoveryDate" || key === "lastContact") {
    const raw = row[key];
    if (!raw) return null;
    const time = new Date(raw).getTime();
    return Number.isNaN(time) ? null : time;
  }
  return row[key];
}

/** Año de descubrimiento en calendario argentino. Si Insight no informó
 * `discoveryDate` se cae a `firstSeenAt`, que es cuándo lo vio esta app —
 * siempre está presente, así que ninguna fila queda fuera del filtro por año. */
export function discoveryYear(row: NewDeviceRow): string {
  const raw = row.discoveryDate ?? row.firstSeenAt;
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return "";
  return toArgDateKey(date).slice(0, 4);
}

/** Años presentes en el listado, del más nuevo al más viejo. */
export function availableYears(rows: readonly NewDeviceRow[]): string[] {
  const years = new Set<string>();
  for (const row of rows) {
    const year = discoveryYear(row);
    if (year) years.add(year);
  }
  return [...years].sort((a, b) => b.localeCompare(a));
}

/** Texto sobre el que corre la búsqueda libre de la barra de acciones. */
export function newDeviceHaystack(row: NewDeviceRow): string {
  return [row.customerName, row.model, row.serial, row.zone, row.ipAddress, row.monitorStatus]
    .join(" ")
    .toLowerCase();
}

/** `monitorStatus` viene de Insight como código de una letra ("X", "I", ...),
 * igual que en la app legacy (`EquiposNuevosView.vue::formatMonitorStatus`).
 * Cualquier valor desconocido cae en `toneForStatusKey`, que devuelve `neutral`. */
export function toneForMonitorStatus(status: string | null | undefined): StatusTone {
  const normalized = (status ?? "").trim();
  if (!normalized) return "neutral";
  if (normalized === "X") return "atencion";
  if (normalized === "I") return "advertencia";
  return toneForStatusKey(normalized) === "neutral" ? "advertencia" : toneForStatusKey(normalized);
}

/** Traduce el código crudo de Insight al texto que mostraba la app legacy
 * (`EquiposNuevosView.vue::formatMonitorStatus`) — portado 1:1. */
export function formatMonitorStatus(status: string | null | undefined): string {
  const normalized = (status ?? "").trim();
  if (!normalized) return "Sin estado";
  if (normalized === "X") return "Deshabilitado";
  if (normalized === "I") return "Solo consumibles";
  return `Sin registrar · ${normalized}`;
}
