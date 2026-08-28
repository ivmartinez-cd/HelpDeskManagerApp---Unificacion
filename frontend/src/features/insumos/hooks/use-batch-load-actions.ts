import { type RefObject, useCallback, useState } from "react";
import { toast } from "sonner";
import { isSelectable } from "../components/dashboard/request-status";
import type { RequestRow } from "../types";
import { partitionBySucursalNotice } from "../utils/sucursal-filter";
import type { DashboardData } from "./use-dashboard-data";
import type { LoadOutcome } from "./use-order-actions-types";
import type { useSucursalNotice } from "./use-sucursal-notice";

type SucursalNoticeApi = ReturnType<typeof useSucursalNotice>;
type RunLoad = (
  row: RequestRow,
  customerId: number,
  customerName: string,
  options?: { forceOverride?: boolean; overrideInsumoId?: string | null },
) => Promise<LoadOutcome>;

/** Carga en lote de las filas seleccionadas de un cliente (con exclusión
 * previa por sucursal y detención ante el primer conflicto) — separado de
 * `use-order-actions.ts` porque ese archivo ya superaba el tamaño máximo de
 * archivo (§4). */
export function useBatchLoadActions(
  dataRef: RefObject<DashboardData>,
  runLoad: RunLoad,
  bulkSucursal: SucursalNoticeApi["bulk"],
  setBulkSucursal: SucursalNoticeApi["setBulk"],
  cancelBulkSucursal: SucursalNoticeApi["clearBulk"],
) {
  const [batchProgress, setBatchProgress] = useState<
    Record<number, { current: number; total: number } | null>
  >({});
  const [batchRunning, setBatchRunning] = useState<Record<number, boolean>>({});

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
    [runLoad, dataRef],
  );

  const loadSelected = useCallback(
    async (customerId: number, customerName: string) => {
      const current = dataRef.current;
      const selectedIds = current.selected[customerId];
      if (!selectedIds || selectedIds.size === 0) return;
      const rows = (current.requestsByCustomer[customerId] ?? []).filter(
        (row) => selectedIds.has(row.requestId) && isSelectable(row),
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
    [runSelectedBatchLoad, dataRef, setBulkSucursal],
  );

  /** El usuario confirmó "Cargar los N restantes" en el modal de exclusión por sucursal. */
  const confirmBulkSucursal = useCallback(async () => {
    const { includedRows, customerId, customerName } = bulkSucursal;
    cancelBulkSucursal();
    if (!customerId || includedRows.length === 0) return;
    await runSelectedBatchLoad(customerId, customerName ?? "", includedRows);
  }, [bulkSucursal, cancelBulkSucursal, runSelectedBatchLoad]);

  return { batchProgress, batchRunning, loadSelected, confirmBulkSucursal };
}
