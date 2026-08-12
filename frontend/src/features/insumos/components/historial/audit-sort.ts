import type { SortValue } from "../../hooks/use-table-sort";
import type { AuditRow } from "../../types";
import { eventLabel } from "./audit-events";

/** Columnas ordenables de la tabla de Historial. "Detalle" y "Acción" quedan
 * afuera a propósito: no tienen un valor natural de columna. */
export const AUDIT_SORT_KEYS = [
  "event",
  "hp_request_time",
  "created_at",
  "customer_name",
  "device_serial",
  "sku",
  "description",
  "initial_percent_left",
  "initial_days_left",
  "initial_pages_left",
  "internal_order_id",
] as const;

export type AuditSortKey = (typeof AUDIT_SORT_KEYS)[number];

/** Las fechas arrancan descendentes: lo más reciente es lo accionable. */
export const AUDIT_DESC_FIRST: readonly AuditSortKey[] = ["hp_request_time", "created_at"];

export const AUDIT_SORT_STORAGE_KEY = "insumos.historial.audit.sort";

/** Valor comparable de cada columna. Las fechas se comparan como timestamp
 * (nunca como texto). `event` ordena por la etiqueta visible (`eventLabel`),
 * no por la clave cruda del backend: si ordenara por `row.event`, "Falsa
 * alarma" (AUTO_DISMISSED) caería bajo la letra A en vez de F. Como bonus,
 * `eventLabel` devuelve "Simulación" cuando `dry_run` es true, así las
 * simulaciones se agrupan tal como se ven en la celda. */
export function auditSortValue(row: AuditRow, key: AuditSortKey): SortValue {
  if (key === "event") return eventLabel(row);
  if (key === "hp_request_time" || key === "created_at") {
    const raw = row[key];
    if (!raw) return null;
    const time = new Date(raw).getTime();
    return Number.isNaN(time) ? null : time;
  }
  return row[key];
}
