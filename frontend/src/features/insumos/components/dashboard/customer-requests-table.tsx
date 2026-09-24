"use client";

import { Fragment } from "react";
import { AlertTriangle, ChevronRight } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import type { DashboardData } from "../../hooks/use-dashboard-data";
import type { OrderActions } from "../../hooks/use-order-actions";
import type { RequestRow } from "../../types";
import { useOptionalTableSort, useSortedRows } from "../../hooks/use-optional-table-sort";
import { SortableHeader, type SortableColumn } from "../shared";
import { CustomerRequestsPanel } from "./customer-requests-panel";
import { CUSTOMER_DESC_FIRST, customerSortValue, type CustomerSortKey } from "./customer-requests-sort";

/** Tabla de clientes con solicitudes pendientes (Patrón 1 del handoff): fila
 * padre = cliente, expandible a la tabla anidada de solicitudes.
 *
 * Se mantienen las 7 columnas del legacy (contadores por severidad) en vez de
 * la grilla `2fr 1fr 1fr 1fr 120px` del mockup: el mockup describe contenido de
 * Contadores, no de Insumos. Lo que sí se toma del Patrón 1 es el caret que
 * rota 90° — sin avatar/iniciales, per handoff sds_insumos.
 */

/** Todas las columnas ordenan; sin orden inicial (se respeta el del backend).
 * La fila expandida viaja con su cliente porque la clave es `customerId`. */
const COLUMNS: readonly SortableColumn<CustomerSortKey>[] = [
  { key: "name", label: "Cliente", className: "text-left" },
  { key: "pending", label: "Pendientes" },
  { key: "critical", label: "Críticos" },
  { key: "urgent", label: "Urgentes" },
  { key: "warning", label: "Atención" },
  { key: "good", label: "OK" },
  { key: "loaded", label: "Cargados" },
];

const HEAD_CELL =
  "px-4 py-2.5 text-right font-body text-[11px] font-semibold uppercase tracking-wider text-muted-foreground";

function CountCell({ value, color }: { value: number; color?: string }) {
  return (
    <td className="px-4 py-2.5 text-right tabular-nums">
      <span
        className={cn("font-semibold", value === 0 && "font-normal text-muted-foreground")}
        style={value > 0 && color ? { color } : undefined}
      >
        {value}
      </span>
    </td>
  );
}

interface CustomerRequestsTableProps {
  data: DashboardData;
  actions: OrderActions;
  canMutate: boolean;
  nowMs: number;
  onOpenDetail: (row: RequestRow) => void;
}

export function CustomerRequestsTable({
  data,
  actions,
  canMutate,
  nowMs,
  onOpenDetail,
}: CustomerRequestsTableProps) {
  const { sort, toggleSort } = useOptionalTableSort(CUSTOMER_DESC_FIRST);
  const customers = useSortedRows(data.customersWithPending, sort, customerSortValue);
  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <table className="w-full border-collapse font-body text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/40">
            {COLUMNS.map((column) => (
              <SortableHeader
                key={column.key}
                column={column}
                sort={sort}
                onToggleSort={toggleSort}
                thClassName={HEAD_CELL}
                buttonClassName="tracking-wider"
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {customers.map((customer) => {
            const expanded = data.expanded.has(customer.customerId);
            return (
              <Fragment key={customer.customerId}>
                <tr
                  className="cursor-pointer select-none border-b border-border/70 transition-colors hover:bg-muted/40"
                  onClick={() => data.toggleExpand(customer.customerId)}
                >
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <ChevronRight
                          className={cn(
                            "h-3.5 w-3.5 flex-none text-muted-foreground transition-transform duration-200",
                            expanded && "rotate-90",
                          )}
                          aria-hidden="true"
                        />
                        <span className="font-semibold text-foreground">{customer.name}</span>
                        {customer.error && (
                          <span
                            title={customer.error}
                            className="inline-flex items-center gap-1 text-xs text-[#dc2626] dark:text-[#f87171]"
                          >
                            <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
                            error de consulta
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums">{customer.pending}</td>
                    <CountCell value={customer.critical} color="#ef4444" />
                    <CountCell value={customer.urgent} color="#F7941D" />
                    <CountCell value={customer.warning} color="#eab308" />
                    <CountCell value={customer.good} color="#22c55e" />
                    <td className="px-4 py-2.5 text-right tabular-nums text-muted-foreground">
                      {customer.loaded}
                    </td>
                  </tr>
                  {expanded && (
                    <tr className="bg-muted/25">
                      <td colSpan={7} className="border-b border-border/70 px-6 py-4">
                        <CustomerRequestsPanel
                          customer={customer}
                          data={data}
                          actions={actions}
                          canMutate={canMutate}
                          nowMs={nowMs}
                          onOpenDetail={onOpenDetail}
                        />
                      </td>
                    </tr>
                  )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
