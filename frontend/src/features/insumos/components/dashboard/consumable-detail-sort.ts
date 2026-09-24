import type { SortValue } from "../../hooks/use-table-sort";
import { cdDateSortValue, isoSortValue } from "../../hooks/use-optional-table-sort";
import type { ConsumableRequestHistoryItem, DeviceSupplyItem } from "../../types";
import { labelled, REASON_LABELS } from "./consumable-detail-primitives";

/** Criterios de orden de las dos tablas del modal de detalle de consumible.
 * Arrancan sin orden (tal como llegan del backend); las fechas, al primer
 * click, muestran lo más reciente primero. */

// ------------------------------------------ Historial de solicitudes (HP SDS)
export type RequestHistorySortKey = "requested" | "requestId" | "reason" | "requestedLevel" | "status";

export const REQUEST_HISTORY_DESC_FIRST: readonly RequestHistorySortKey[] = ["requested"];

export function requestHistorySortValue(
  item: ConsumableRequestHistoryItem,
  key: RequestHistorySortKey,
): SortValue {
  switch (key) {
    case "requested":
      return isoSortValue(item.requested);
    case "reason":
      // Por la etiqueta visible ("Nivel bajo"), no por la clave cruda.
      return item.reason ? labelled(REASON_LABELS, item.reason) : null;
    case "status":
      return item.statusLabel;
    default:
      return item[key];
  }
}

// ----------------------------------------- Pedidos recientes en Canal Directo
export type SupplySortKey = "fecha" | "sku" | "descripcion" | "estado";

export const SUPPLY_DESC_FIRST: readonly SupplySortKey[] = ["fecha"];

/** `fecha` viene en el formato de Canal Directo (`DD/MM/YYYY HH:MM:SS`): se
 * compara como fecha, nunca como texto (si no, ordenaría por día del mes). */
export function supplySortValue(item: DeviceSupplyItem, key: SupplySortKey): SortValue {
  return key === "fecha" ? cdDateSortValue(item.fecha) : item[key];
}
