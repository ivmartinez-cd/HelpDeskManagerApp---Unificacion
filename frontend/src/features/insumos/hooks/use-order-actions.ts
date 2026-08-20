"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { insumosApi } from "../api/insumos-api";
import type {
  BulkSucursalState,
  SucursalNoticeState,
} from "../components/dashboard/dashboard-sucursal-modals";
import { isLoaded } from "../components/dashboard/request-status";
import type { RequestRow } from "../types";
import { partitionBySucursalNotice } from "../utils/sucursal-filter";
import type { DashboardData } from "./use-dashboard-data";
import { useSucursalNotice } from "./use-sucursal-notice";

/** Acciones de negocio del Dashboard (cargar / descartar, individual y en
 * lote) + el estado de los 5 modales de conflicto.
 *
 * Port de `useOrderActions.ts` + `useDashboardModals.ts`. Dos diferencias
 * deliberadas con el legacy:
 *
 * 1. **Un solo estado de modal** (unión discriminada) en vez de 5 `ref`
 *    independientes: nunca puede haber dos abiertos a la vez, y con 5 estados
 *    sueltos era posible dejar uno "visible: false" con su `pendingRow` viejo.
 * 2. **La carga en lote se detiene** si el backend devuelve un conflicto. El
 *    legacy seguía iterando y cada conflicto pisaba el modal del anterior, así
 *    que el operador solo veía el último y los demás se perdían en silencio.
 *
 * TRAMPA del contrato: `/load` y `/dismiss` responden HTTP 200 aunque fallen —
 * el error de negocio viaja en el body (`ok: false` + `error`/`conflictType`).
 * `httpClient` NO tira `ApiError` en ese caso: hay que ramificar por
 * `response.ok` a mano. El `catch` de acá cubre solo errores de red/HTTP.
 */

/** Los cuatro `conflictType` que emite el backend, en
 * `application/dtos/load_order.py`. `AMBIGUOUS_INSUMO` va en mayúsculas a
 * propósito (casing heredado del legacy). */
export const CONFLICT_PENDING_VALIDATION = "pending_validation";
export const CONFLICT_TODAY_ORDER = "today_order";
export const CONFLICT_ACTIVE_SUPPLY = "active_supply";
export const CONFLICT_AMBIGUOUS_INSUMO = "AMBIGUOUS_INSUMO";

export type DuplicateConflictType = typeof CONFLICT_TODAY_ORDER | typeof CONFLICT_ACTIVE_SUPPLY;

interface ModalTarget {
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

type LoadOutcome = "success" | "conflict" | "error";

function errorMessage(error: unknown): string {
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

export function useOrderActions(data: DashboardData): OrderActions {
  const [modal, setModal] = useState<DashboardModal | null>(null);
  const [modalBusy, setModalBusy] = useState(false);
  const [loadingRows, setLoadingRows] = useState<ReadonlySet<number>>(() => new Set<number>());
  const [rowErrors, setRowErrors] = useState<ReadonlyMap<number, string>>(
    () => new Map<number, string>(),
  );
  const [batchProgress, setBatchProgress] = useState<
    Record<number, { current: number; total: number } | null>
  >({});
  const [batchRunning, setBatchRunning] = useState<Record<number, boolean>>({});
  const {
    notice: sucursalNotice,
    setNotice: setSucursalNotice,
    closeNotice: closeSucursalNotice,
    bulk: bulkSucursal,
    setBulk: setBulkSucursal,
    clearBulk: cancelBulkSucursal,
  } = useSucursalNotice();

  // Los callbacks de abajo se declaran con deps vacías (identidad estable para
  // no re-renderizar cada fila de la tabla en cada tick del countdown), así que
  // leen los datos frescos por ref en vez de por closure.
  const dataRef = useRef(data);
  useEffect(() => {
    dataRef.current = data;
  }, [data]);

  const setRowError = useCallback((requestId: number, message: string | null) => {
    setRowErrors((state) => {
      const next = new Map(state);
      if (message === null) next.delete(requestId);
      else next.set(requestId, message);
      return next;
    });
  }, []);

  const runLoad = useCallback(
    async (
      row: RequestRow,
      customerId: number,
      customerName: string,
      options: { forceOverride?: boolean; overrideInsumoId?: string | null } = {},
    ): Promise<LoadOutcome> => {
      setLoadingRows((state) => new Set(state).add(row.requestId));
      setRowError(row.requestId, null);
      try {
        const response = await insumosApi.loadRequest(row.requestId, {
          customerId,
          customerName,
          forceOverride: options.forceOverride ?? false,
          overrideInsumoId: options.overrideInsumoId ?? null,
        });

        if (!response.ok) {
          const target = { row, customerId, customerName };
          if (response.conflictType === CONFLICT_AMBIGUOUS_INSUMO && response.options?.length) {
            setModal({ kind: "ambiguous", ...target, options: response.options });
            return "conflict";
          }
          if (response.conflictType === CONFLICT_PENDING_VALIDATION) {
            setModal({ kind: "validation", ...target, conflictData: response.conflictData ?? null });
            return "conflict";
          }
          if (
            (response.conflictType === CONFLICT_TODAY_ORDER ||
              response.conflictType === CONFLICT_ACTIVE_SUPPLY) &&
            response.conflictData
          ) {
            setModal({
              kind: "duplicate",
              ...target,
              conflictType: response.conflictType,
              conflictData: response.conflictData,
            });
            return "conflict";
          }
          const message = response.error ?? "No se pudo cargar el pedido";
          setRowError(row.requestId, message);
          toast.error(message);
          return "error";
        }

        toast.success(`Pedido creado: ${response.orderId ?? "sin número"}`);
        if (response.warn) toast.warning(response.warn);
        // Zona con instrucción de entrega alternativa ("CARGAR PARA SUCURSAL: ..."):
        // el pedido ya se creó, esto es un recordatorio para cambiarla a mano en CD.
        if (response.requiereCambioSucursal) {
          setSucursalNotice({
            visible: true,
            orderId: response.orderId ?? null,
            supplyUrl: response.supplyUrl ?? null,
            sucursal: response.sucursalEntrega ?? null,
            observacion: response.observacionZona ?? "",
          });
        }
        return "success";
      } catch (err) {
        const message = errorMessage(err);
        setRowError(row.requestId, message);
        toast.error(message);
        return "error";
      } finally {
        setLoadingRows((state) => {
          const next = new Set(state);
          next.delete(row.requestId);
          return next;
        });
      }
    },
    [setRowError, setSucursalNotice],
  );

  const loadSingle = useCallback(
    async (row: RequestRow, customerId: number, customerName: string) => {
      // Bloqueo client-side: el equipo lleva días sin reportar, el nivel que se
      // ve puede ser viejo (posible bodega). El backend no lo chequea.
      if (row.isStaleOffline) {
        setModal({ kind: "stale", row, customerId, customerName });
        return;
      }
      const outcome = await runLoad(row, customerId, customerName);
      if (outcome === "success") await dataRef.current.refreshCustomer(customerId);
    },
    [runLoad],
  );

  const runSelectedBatchLoad = useCallback(
    async (customerId: number, customerName: string, rows: RequestRow[]) => {
      if (rows.length === 0) return;

      setBatchRunning((state) => ({ ...state, [customerId]: true }));
      let loaded = 0;
      let errors = 0;
      let stopped = false;

      for (const [index, row] of rows.entries()) {
        setBatchProgress((state) => ({
          ...state,
          [customerId]: { current: index + 1, total: rows.length },
        }));
        const outcome = await runLoad(row, customerId, customerName);
        if (outcome === "success") {
          loaded += 1;
          dataRef.current.deselect(customerId, row.requestId);
        } else if (outcome === "conflict") {
          stopped = true;
          break;
        } else {
          errors += 1;
        }
      }

      setBatchRunning((state) => ({ ...state, [customerId]: false }));
      setBatchProgress((state) => ({ ...state, [customerId]: null }));

      if (stopped) {
        toast.warning(
          `${loaded} pedido(s) cargado(s). La carga en lote se detuvo: hay un conflicto para resolver.`,
        );
      } else if (errors > 0) {
        toast.warning(`${loaded} cargado(s) · ${errors} error(es)`);
      } else {
        toast.success(`${loaded} pedido(s) cargado(s)`);
      }

      await dataRef.current.refreshCustomer(customerId);
    },
    [runLoad],
  );

  const loadSelected = useCallback(
    async (customerId: number, customerName: string) => {
      const current = dataRef.current;
      const selectedIds = current.selected[customerId];
      if (!selectedIds || selectedIds.size === 0) return;
      const rows = (current.requestsByCustomer[customerId] ?? []).filter(
        (row) => selectedIds.has(row.requestId) && !isLoaded(row),
      );
      if (rows.length === 0) return;

      // Zonas con instrucción de entrega alternativa quedan fuera del lote: se
      // avisan y se cargan de a una para no perder el recordatorio de sucursal.
      const { included, excluded } = partitionBySucursalNotice(rows);
      if (excluded.length > 0) {
        setBulkSucursal({
          visible: true,
          excluded,
          includedCount: included.length,
          includedRows: included,
          customerId,
          customerName,
        });
        return;
      }

      await runSelectedBatchLoad(customerId, customerName, rows);
    },
    [runSelectedBatchLoad, setBulkSucursal],
  );

  /** El usuario confirmó "Cargar los N restantes" en el modal de exclusión por sucursal. */
  const confirmBulkSucursal = useCallback(async () => {
    const { includedRows, customerId, customerName } = bulkSucursal;
    cancelBulkSucursal();
    if (!customerId || includedRows.length === 0) return;
    await runSelectedBatchLoad(customerId, customerName ?? "", includedRows);
  }, [bulkSucursal, cancelBulkSucursal, runSelectedBatchLoad]);

  const dismissSingle = useCallback(
    async (row: RequestRow, customerId: number, customerName: string): Promise<boolean> => {
      setRowError(row.requestId, null);
      try {
        const response = await insumosApi.dismissRequest(row.requestId, {
          customerId,
          customerName,
          serial: row.serial,
          sku: row.sku,
        });
        if (!response.ok) {
          setRowError(row.requestId, response.error ?? "Error al descartar");
          return false;
        }
        return true;
      } catch (err) {
        setRowError(row.requestId, errorMessage(err));
        return false;
      }
    },
    [setRowError],
  );

  const confirmDismiss = useCallback(async () => {
    const current = modal;
    if (current?.kind !== "dismiss") return;
    const { row, customerId, customerName } = current;

    if (row) {
      const ok = await dismissSingle(row, customerId, customerName);
      if (!ok) {
        toast.error(`No se pudo descartar la solicitud ${row.requestId}`);
        return;
      }
      toast.success("Solicitud descartada en HP SDS");
      setModal(null);
      await dataRef.current.refreshCustomer(customerId);
      return;
    }

    const data_ = dataRef.current;
    const selectedIds = data_.selected[customerId];
    const rows = (data_.requestsByCustomer[customerId] ?? []).filter(
      (candidate) => selectedIds?.has(candidate.requestId) && !isLoaded(candidate),
    );

    let dismissed = 0;
    let errors = 0;
    for (const candidate of rows) {
      const ok = await dismissSingle(candidate, customerId, customerName);
      if (ok) {
        dismissed += 1;
        dataRef.current.deselect(customerId, candidate.requestId);
      } else {
        errors += 1;
      }
    }
    if (errors > 0) toast.warning(`${dismissed} descartadas · ${errors} error(es)`);
    else toast.success(`${dismissed} solicitudes descartadas`);

    setModal(null);
    await dataRef.current.refreshCustomer(customerId);
  }, [modal, dismissSingle]);

  const confirmModal = useCallback(
    async (selectedInsumoId?: string) => {
      const current = modal;
      if (!current || modalBusy) return;
      setModalBusy(true);
      try {
        if (current.kind === "dismiss") {
          await confirmDismiss();
          return;
        }
        const { row, customerId, customerName } = current;
        const options =
          current.kind === "ambiguous"
            ? { overrideInsumoId: selectedInsumoId ?? null }
            : // `stale` es un bloqueo puramente client-side: el backend no lo
              // conoce, así que se reintenta SIN forceOverride para no saltear
              // de paso los bloqueos reales de servidor.
              { forceOverride: current.kind !== "stale" };
        const outcome = await runLoad(row, customerId, customerName, options);
        if (outcome !== "conflict") setModal(null);
        if (outcome === "success") await dataRef.current.refreshCustomer(customerId);
      } finally {
        setModalBusy(false);
      }
    },
    [modal, modalBusy, confirmDismiss, runLoad],
  );

  const openDismiss = useCallback((row: RequestRow, customerId: number, customerName: string) => {
    setModal({ kind: "dismiss", row, customerId, customerName, count: 1 });
  }, []);

  const openBatchDismiss = useCallback((customerId: number, customerName: string) => {
    const selectedIds = dataRef.current.selected[customerId];
    if (!selectedIds || selectedIds.size === 0) return;
    setModal({ kind: "dismiss", row: null, customerId, customerName, count: selectedIds.size });
  }, []);

  const openValidationOverride = useCallback(
    (row: RequestRow, customerId: number, customerName: string) => {
      setModal({ kind: "validation", row, customerId, customerName, conflictData: null });
    },
    [],
  );

  const closeModal = useCallback(() => {
    if (!modalBusy) setModal(null);
  }, [modalBusy]);

  return {
    modal,
    modalBusy,
    loadingRows,
    rowErrors,
    batchProgress,
    batchRunning,
    sucursalNotice,
    closeSucursalNotice,
    bulkSucursalModal: bulkSucursal,
    confirmBulkSucursal,
    cancelBulkSucursal,
    closeModal,
    loadSingle,
    loadSelected,
    openDismiss,
    openBatchDismiss,
    openValidationOverride,
    confirmModal,
  };
}
