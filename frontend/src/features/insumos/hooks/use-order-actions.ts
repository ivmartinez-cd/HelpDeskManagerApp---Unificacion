"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { insumosApi } from "../api/insumos-api";
import type { RequestRow } from "../types";
import type { DashboardData } from "./use-dashboard-data";
import { useBatchLoadActions } from "./use-batch-load-actions";
import { useDismissActions } from "./use-dismiss-actions";
import {
  CONFLICT_ACTIVE_SUPPLY,
  CONFLICT_AMBIGUOUS_INSUMO,
  CONFLICT_PENDING_VALIDATION,
  CONFLICT_TODAY_ORDER,
  type DashboardModal,
  type DuplicateConflictType,
  errorMessage,
  type LoadOutcome,
  type ModalTarget,
  type OrderActions,
} from "./use-order-actions-types";
import { useSucursalNotice } from "./use-sucursal-notice";

export {
  CONFLICT_ACTIVE_SUPPLY,
  CONFLICT_AMBIGUOUS_INSUMO,
  CONFLICT_PENDING_VALIDATION,
  CONFLICT_TODAY_ORDER,
};
export type { DashboardModal, DuplicateConflictType, ModalTarget, OrderActions };

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
 *
 * El descarte (individual y en lote) vive en `use-dismiss-actions.ts` —
 * separado porque este archivo ya superaba el tamaño máximo de archivo (§4).
 */
export function useOrderActions(data: DashboardData): OrderActions {
  const [modal, setModal] = useState<DashboardModal | null>(null);
  const [modalBusy, setModalBusy] = useState(false);
  const [loadingRows, setLoadingRows] = useState<ReadonlySet<number>>(() => new Set<number>());
  const [rowErrors, setRowErrors] = useState<ReadonlyMap<number, string>>(
    () => new Map<number, string>(),
  );
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

  const { confirmDismiss, openDismiss, openBatchDismiss } = useDismissActions(
    dataRef,
    setRowError,
    modal,
    setModal,
  );

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

  const { batchProgress, batchRunning, loadSelected, confirmBulkSucursal } = useBatchLoadActions(
    dataRef,
    runLoad,
    bulkSucursal,
    setBulkSucursal,
    cancelBulkSucursal,
  );

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
