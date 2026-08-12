import type { OfflineDeviceRow } from "../../types";
import type { SortValue } from "../../hooks/use-table-sort";

/** Las 6 secciones de EquiposOfflineView, en el orden en que se muestran.
 * "caida_colector" tiene máxima precedencia: un equipo en un outage va ahí
 * sin importar cuál sea su cdStatus (portado de `groupKeyOf` del legacy). */
export type OfflineGroup =
  | "caida_colector"
  | "bodega"
  | "sin_verificar"
  | "error"
  | "otro_cliente"
  | "en_cliente";

export const OFFLINE_GROUP_ORDER: readonly OfflineGroup[] = [
  "caida_colector",
  "bodega",
  "sin_verificar",
  "error",
  "otro_cliente",
  "en_cliente",
];

export interface OfflineGroupMeta {
  label: string;
  description: string;
  /** El grupo arranca expandido cuando tiene filas (salvo "en_cliente"). */
  defaultExpanded: boolean;
}

export const OFFLINE_GROUP_META: Record<OfflineGroup, OfflineGroupMeta> = {
  caida_colector: {
    label: "Caída de colector",
    description: "Equipos de un cliente con caída masiva — excluidos de la baja automática.",
    defaultExpanded: true,
  },
  bodega: {
    label: "En bodega",
    description: "Veredicto Canal Directo: el equipo está en bodega. Son los candidatos a baja.",
    defaultExpanded: true,
  },
  sin_verificar: {
    label: "Sin verificar",
    description: "Todavía no se consultó Canal Directo para este equipo.",
    defaultExpanded: true,
  },
  error: {
    label: "Error de verificación",
    description: "La consulta a Canal Directo falló o devolvió un error inesperado.",
    defaultExpanded: true,
  },
  otro_cliente: {
    label: "En otro cliente",
    description: "Canal Directo ubica el equipo bajo un cliente diferente al actual.",
    defaultExpanded: false,
  },
  en_cliente: {
    label: "En cliente",
    description:
      "Canal Directo confirma que sigue en el cliente — puede ser un falso positivo de offline.",
    defaultExpanded: false,
  },
};

export function groupKeyOf(row: OfflineDeviceRow): OfflineGroup {
  if (row.inMassOutage) return "caida_colector";
  switch (row.cdStatus) {
    case "BODEGA":
      return "bodega";
    case "OTRO_CLIENTE":
      return "otro_cliente";
    case "EN_CLIENTE":
      return "en_cliente";
    case "ERROR":
      return "error";
    default:
      return "sin_verificar";
  }
}

// ---------------------------------------------------------------- Sort keys

export const OFFLINE_SORT_KEYS = [
  "customerName",
  "serial",
  "model",
  "zone",
  "lastContact",
  "daysOffline",
  "cdStatus",
] as const;

export type OfflineSortKey = (typeof OFFLINE_SORT_KEYS)[number];

export const OFFLINE_DESC_FIRST: readonly OfflineSortKey[] = ["lastContact", "daysOffline"];

export const OFFLINE_SORT_STORAGE_KEY = "equipos-offline-sort";

export function offlineSortValue(row: OfflineDeviceRow, key: OfflineSortKey): SortValue {
  switch (key) {
    case "customerName":
      return row.customerName;
    case "serial":
      return row.serial;
    case "model":
      return row.model;
    case "zone":
      return row.zone;
    case "lastContact":
      return row.lastContact ?? null;
    case "daysOffline":
      return row.daysOffline ?? null;
    case "cdStatus":
      return row.cdStatus;
  }
}

export function offlineHaystack(row: OfflineDeviceRow): string {
  return [row.serial, row.model, row.customerName, row.zone, row.cdDetail]
    .join(" ")
    .toLowerCase();
}
