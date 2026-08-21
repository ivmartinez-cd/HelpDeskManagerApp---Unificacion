import type {
  BulkSucursalState,
  SucursalNoticeState,
} from "../components/dashboard/dashboard-sucursal-modals";
import type { RequestRow } from "../types";

/** Tipos y constantes de `use-order-actions.ts`, separados porque ese archivo
 * ya superaba el tamaño máximo de archivo (§4).
 *
 * Los cuatro `conflictType` que emite el backend, en
 * `application/dtos/load_order.py`. `AMBIGUOUS_INSUMO` va en mayúsculas a
 * propósito (casing heredado del legacy). */
export const CONFLICT_PENDING_VALIDATION = "pending_validation";
export const CONFLICT_TODAY_ORDER = "today_order";
export const CONFLICT_ACTIVE_SUPPLY = "active_supply";
export const CONFLICT_AMBIGUOUS_INSUMO = "AMBIGUOUS_INSUMO";

export type DuplicateConflictType = typeof CONFLICT_TODAY_ORDER | typeof CONFLICT_ACTIVE_SUPPLY;

export interface ModalTarget {
  row: RequestRow;
  customerId: number;
  customerName: string;
}

export type DashboardModal =
  | (ModalTarget & {
      kind: "duplicate";
      conflictType: DuplicateConflictType;
      conflictData: Record<string, unknown>;
    })
  | (ModalTarget & { kind: "ambiguous"; options: Record<string, string>[] })
  | (ModalTarget & { kind: "stale" })
  | (ModalTarget & { kind: "validation"; conflictData: Record<string, unknown> | null })
  | {
      kind: "dismiss";
      /** `null` = descarte en lote; con fila = descarte individual. */
      row: RequestRow | null;
      customerId: number;
      customerName: string;
      count: number;
    };

export type LoadOutcome = "success" | "conflict" | "error";

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Error desconocido";
}

export interface OrderActions {
  modal: DashboardModal | null;
  modalBusy: boolean;
  loadingRows: ReadonlySet<number>;
  rowErrors: ReadonlyMap<number, string>;
  batchProgress: Record<number, { current: number; total: number } | null>;
  batchRunning: Record<number, boolean>;
  /** Aviso recordatorio post-carga individual (ver dashboard-sucursal-modals.tsx). */
  sucursalNotice: SucursalNoticeState;
  closeSucursalNotice: () => void;
  /** Exclusión previa a "Cargar seleccionados" cuando hay filas con el aviso. */
  bulkSucursalModal: BulkSucursalState;
  confirmBulkSucursal: () => Promise<void>;
  cancelBulkSucursal: () => void;
  closeModal: () => void;
  loadSingle: (row: RequestRow, customerId: number, customerName: string) => Promise<void>;
  loadSelected: (customerId: number, customerName: string) => Promise<void>;
  openDismiss: (row: RequestRow, customerId: number, customerName: string) => void;
  openBatchDismiss: (customerId: number, customerName: string) => void;
  openValidationOverride: (row: RequestRow, customerId: number, customerName: string) => void;
  confirmModal: (selectedInsumoId?: string) => Promise<void>;
}
