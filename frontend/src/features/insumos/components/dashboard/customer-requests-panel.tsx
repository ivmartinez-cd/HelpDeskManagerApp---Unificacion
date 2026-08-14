"use client";

import { useEffect, useRef } from "react";
import { AlertTriangle, Loader2 } from "lucide-react";
import type { DashboardData } from "../../hooks/use-dashboard-data";
import { isCountdownExpired } from "../../hooks/use-countdown-clock";
import type { OrderActions } from "../../hooks/use-order-actions";
import type { CustomerSummary, RequestRow as RequestRowType } from "../../types";
import { RequestRow } from "./request-row";

/** Panel expandido de un cliente: toolbar de acciones masivas + tabla anidada
 * de solicitudes pendientes. Es el contenido de la fila expandida del Patrón 1.
 */

const HEAD_CELL = "px-2 py-2 text-left font-semibold";

interface CustomerRequestsPanelProps {
  customer: CustomerSummary;
  data: DashboardData;
  actions: OrderActions;
  canMutate: boolean;
  nowMs: number;
  onOpenDetail: (row: RequestRowType) => void;
}

export function CustomerRequestsPanel({
  customer,
  data,
  actions,
  canMutate,
  nowMs,
  onOpenDetail,
}: CustomerRequestsPanelProps) {
  const customerId = customer.customerId;
  const rows = data.pendingRequests(customerId);
  const selectedIds = data.selected[customerId];
  const selectedCount = selectedIds?.size ?? 0;
  const batchRunning = actions.batchRunning[customerId] ?? false;
  const progress = actions.batchProgress[customerId];

  // Cuando el countdown de una fila "Validando" llega a 00:00 la ventana ya
  // venció del lado del backend, pero esta tabla sigue mostrando la foto vieja:
  // el poll de /dashboard solo re-pide /requests si cambió la cantidad de
  // pendientes, y una validación resuelta no la cambia. Sin este refetch el
  // operador se queda mirando "Validando 00:00" sin botones. Una sola vez por
  // solicitud, para no reintentar en cada tick del reloj.
  const expiredNotified = useRef<Set<number>>(new Set());
  useEffect(() => {
    const expired = rows.filter(
      (row) =>
        row.validationPending &&
        isCountdownExpired(row.validationDeadline, nowMs) &&
        !expiredNotified.current.has(row.requestId),
    );
    if (expired.length === 0) return;
    for (const row of expired) expiredNotified.current.add(row.requestId);
    void data.fetchCustomerRequests(customerId);
  }, [rows, nowMs, customerId, data]);

  if (data.requestsLoading[customerId]) {
    return (
      <div className="flex items-center justify-center gap-2 py-6 font-body text-xs text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin text-brand-orange" aria-hidden="true" />
        Cargando solicitudes de insumos…
      </div>
    );
  }

  const error = data.requestsError[customerId];
  if (error) {
    return (
      <div className="flex items-center justify-center gap-2 py-6 font-body text-xs text-[#dc2626]">
        <AlertTriangle className="h-4 w-4" aria-hidden="true" />
        Error al cargar solicitudes: {error}
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="py-6 text-center font-body text-xs text-muted-foreground">
        No hay solicitudes pendientes para este cliente.
      </div>
    );
  }

  return (
    <div className="rounded-[12px] border border-border bg-card p-4">
      <div className="mb-3 flex flex-wrap items-center gap-4 border-b border-border pb-3">
        <div className="font-body text-xs font-bold text-foreground">
          Solicitudes de {customer.name} ({rows.length})
        </div>
        {canMutate && (
          <div className="ml-auto flex items-center gap-2.5">
            <button
              type="button"
              disabled={batchRunning || selectedCount === 0}
              onClick={() => void actions.loadSelected(customerId, customer.name)}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-[8px] bg-brand-orange px-3 py-1.5 font-body text-xs font-bold text-white transition-colors hover:bg-brand-orange-hover disabled:cursor-not-allowed disabled:opacity-50"
            >
              {batchRunning && <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />}
              {batchRunning && progress
                ? `Cargando ${progress.current} / ${progress.total}`
                : `Cargar seleccionados (${selectedCount})`}
            </button>
            <button
              type="button"
              disabled={batchRunning || selectedCount === 0}
              onClick={() => actions.openBatchDismiss(customerId, customer.name)}
              className="cursor-pointer rounded-[8px] border border-[rgba(239,68,68,.35)] px-3 py-1.5 font-body text-xs font-bold text-[#dc2626] transition-colors hover:bg-[rgba(239,68,68,.08)] disabled:cursor-not-allowed disabled:opacity-50 dark:text-[#f87171]"
            >
              Descartar seleccionados ({selectedCount})
            </button>
          </div>
        )}
      </div>

      <div className="overflow-x-auto thin-scrollbar">
        <table className="w-full border-collapse font-body text-xs">
          <thead>
            <tr className="border-b border-border text-muted-foreground">
              <th className={`${HEAD_CELL} w-8`}>
                <input
                  type="checkbox"
                  checked={data.isAllSelected(customerId)}
                  disabled={batchRunning || rows.length === 0 || !canMutate}
                  onChange={() => data.toggleSelectAll(customerId)}
                  aria-label="Seleccionar todas las solicitudes"
                  className="cursor-pointer accent-brand-orange"
                />
              </th>
              <th className={HEAD_CELL}>Solicitud</th>
              <th className={HEAD_CELL}>Sucursal</th>
              <th className={HEAD_CELL}>Serie</th>
              <th className={HEAD_CELL}>Descripción</th>
              <th className={HEAD_CELL}>SKU</th>
              <th className={`${HEAD_CELL} text-right`}>%</th>
              <th className={`${HEAD_CELL} text-right`}>Días rest.</th>
              <th className={`${HEAD_CELL} text-right`}>Págs. rest.</th>
              <th className={HEAD_CELL}>Estado</th>
              <th className={`${HEAD_CELL} w-36`}>Acción</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <RequestRow
                key={row.requestId}
                row={row}
                selected={selectedIds?.has(row.requestId) ?? false}
                canMutate={canMutate}
                loading={actions.loadingRows.has(row.requestId)}
                batchRunning={batchRunning}
                error={actions.rowErrors.get(row.requestId)}
                nowMs={nowMs}
                onToggleSelect={() => data.toggleSelect(customerId, row.requestId)}
                onLoad={() => void actions.loadSingle(row, customerId, customer.name)}
                onDismiss={() => actions.openDismiss(row, customerId, customer.name)}
                onValidationOverride={() =>
                  actions.openValidationOverride(row, customerId, customer.name)
                }
                onOpenDetail={() => onOpenDetail(row)}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
