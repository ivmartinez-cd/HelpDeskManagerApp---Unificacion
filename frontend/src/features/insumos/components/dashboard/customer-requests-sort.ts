import type { SortValue } from "../../hooks/use-table-sort";
import { isoSortValue } from "../../hooks/use-optional-table-sort";
import type { CustomerSummary, RequestRow } from "../../types";

/** Criterios de orden de las dos tablas del Dashboard: la de clientes (fila
 * padre) y la de solicitudes del panel expandido. Ambas arrancan sin orden
 * (tal como las devuelve el backend) hasta que el usuario clickea un header. */

// ------------------------------------------------------ Tabla de clientes
export type CustomerSortKey = Exclude<keyof CustomerSummary, "customerId" | "error">;

/** Contadores: el primer click muestra primero a quien más tiene. */
export const CUSTOMER_DESC_FIRST: readonly CustomerSortKey[] = [
  "pending",
  "critical",
  "urgent",
  "warning",
  "good",
  "loaded",
];

export function customerSortValue(row: CustomerSummary, key: CustomerSortKey): SortValue {
  return row[key];
}

// ------------------------------------------- Solicitudes del panel expandido
export type RequestSortKey =
  | "time"
  | "store"
  | "serial"
  | "description"
  | "sku"
  | "percentLeft"
  | "daysLeft"
  | "pagesLeft"
  | "status";

/** La fecha arranca descendente (lo más reciente primero). */
export const REQUEST_DESC_FIRST: readonly RequestSortKey[] = ["time"];

/** "Estado" ordena por gravedad (crítico → OK), no alfabéticamente por la
 * etiqueta: ascendente deja arriba lo más urgente. */
const SEVERITY_RANK: Record<string, number> = { critical: 0, urgent: 1, warning: 2, good: 3 };

export function requestSortValue(row: RequestRow, key: RequestSortKey): SortValue {
  switch (key) {
    case "time":
      return isoSortValue(row.rawTime);
    case "status":
      return SEVERITY_RANK[row.statusKey] ?? null;
    default:
      return row[key];
  }
}
