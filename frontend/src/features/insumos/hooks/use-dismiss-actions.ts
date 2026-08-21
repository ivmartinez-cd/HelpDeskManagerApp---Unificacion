import { type RefObject, useCallback } from "react";
import { toast } from "sonner";
import { insumosApi } from "../api/insumos-api";
import { isLoaded } from "../components/dashboard/request-status";
import type { RequestRow } from "../types";
import type { DashboardData } from "./use-dashboard-data";
import { type DashboardModal, errorMessage } from "./use-order-actions-types";

/** Descarte de solicitudes (individual y en lote), separado de
 * `use-order-actions.ts` porque ese archivo ya superaba el tamaño máximo de
 * archivo (§4). Comparte el estado de modal/rowErrors del hook padre en vez
 * de tener el suyo propio — nunca hay dos modales abiertos a la vez. */
export function useDismissActions(
  dataRef: RefObject<DashboardData>,
  setRowError: (requestId: number, message: string | null) => void,
  modal: DashboardModal | null,
  setModal: (modal: DashboardModal | null) => void,
) {
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
  }, [modal, dismissSingle, dataRef, setModal]);

  const openDismiss = useCallback(
    (row: RequestRow, customerId: number, customerName: string) => {
      setModal({ kind: "dismiss", row, customerId, customerName, count: 1 });
    },
    [setModal],
  );

  const openBatchDismiss = useCallback(
    (customerId: number, customerName: string) => {
      const selectedIds = dataRef.current.selected[customerId];
      if (!selectedIds || selectedIds.size === 0) return;
      setModal({ kind: "dismiss", row: null, customerId, customerName, count: selectedIds.size });
    },
    [dataRef, setModal],
  );

  return { confirmDismiss, openDismiss, openBatchDismiss };
}
