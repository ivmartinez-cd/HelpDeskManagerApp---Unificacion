"use client";

import { ExternalLink } from "lucide-react";
import {
  SortableHeader,
  StatusBadge,
  TonerBar,
  toneForStatusKey,
  type SortableColumn,
} from "../shared";
import type { PendingOrderRow } from "../../types";
import { EMPTY_VALUE, formatArgDateTime } from "../../utils/format";
import { isoSortValue, useOptionalTableSort, useSortedRows } from "../../hooks/use-optional-table-sort";
import type { SortValue } from "../../hooks/use-table-sort";
import { sdsDeviceUrl } from "./audit-events";

/** Sub-tabla de la fila expandida de "Pedidos Pendientes": un renglón por
 * pedido del cliente. Cada métrica muestra el valor de hoy y, abajo, el valor
 * "Ini:" del momento en que se cargó el pedido — la diferencia entre los dos
 * es lo que delata un consumible ya cambiado con el pedido todavía abierto. */

const thClass =
  "whitespace-nowrap px-2 py-2 text-left font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground";
type OrderSortKey =
  | "store"
  | "serial"
  | "description"
  | "sku"
  | "currentPercentLeft"
  | "currentDaysLeft"
  | "currentPagesLeft"
  | "supplyStatus"
  | "orderId"
  | "createdAt";

/** Todas las columnas ordenan. Las métricas ordenan por el valor de HOY (el
 * grande de la celda), "Estado" por el estado en Canal Directo y "Cargado el"
 * como fecha. Sin orden inicial: se respeta el del backend (más viejos primero). */
const COLUMNS: readonly SortableColumn<OrderSortKey>[] = [
  { key: "store", label: "Sucursal" },
  { key: "serial", label: "Serie" },
  { key: "description", label: "Insumo" },
  { key: "sku", label: "SKU" },
  { key: "currentPercentLeft", label: "Nivel", className: "text-right" },
  { key: "currentDaysLeft", label: "Días rest.", className: "text-right" },
  { key: "currentPagesLeft", label: "Págs. rest.", className: "text-right" },
  { key: "supplyStatus", label: "Estado" },
  { key: "orderId", label: "Pedido CD" },
  { key: "createdAt", label: "Cargado el" },
];
const DESC_FIRST: readonly OrderSortKey[] = ["createdAt"];

function orderSortValue(order: PendingOrderRow, key: OrderSortKey): SortValue {
  return key === "createdAt" ? isoSortValue(order.createdAt) : order[key];
}

const tdClass = "px-2 py-2 font-body text-[12px] text-foreground";
const iniClass = "font-body text-[10.5px] text-muted-foreground";

export function PendingOrdersDetail({ orders }: { orders: PendingOrderRow[] }) {
  const { sort, toggleSort } = useOptionalTableSort(DESC_FIRST);
  const sortedOrders = useSortedRows(orders, sort, orderSortValue);
  return (
    <div className="overflow-x-auto rounded-[8px] border border-border bg-card">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-border">
            {COLUMNS.map((column) => (
              <SortableHeader
                key={column.key}
                column={column}
                sort={sort}
                onToggleSort={toggleSort}
                thClassName={thClass}
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedOrders.map((order) => {
            const deviceUrl = sdsDeviceUrl(order.deviceId);
            return (
              <tr key={order.hpRequestId} className="border-b border-border last:border-0">
                <td className={tdClass}>{order.store || EMPTY_VALUE}</td>
                <td className={`${tdClass} font-mono`}>
                  {deviceUrl ? (
                    <a
                      href={deviceUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-brand-orange hover:underline"
                    >
                      {order.serial}
                      <ExternalLink className="h-3 w-3" aria-hidden="true" />
                    </a>
                  ) : (
                    order.serial
                  )}
                </td>
                <td className={`${tdClass} max-w-[170px] truncate`} title={order.description}>
                  {order.description}
                </td>
                <td className={`${tdClass} font-mono text-[11px] text-muted-foreground`}>
                  {order.sku}
                </td>
                <td className={tdClass}>
                  <div className="flex w-[120px] flex-col items-end gap-0.5">
                    <TonerBar percent={order.currentPercentLeft} showValue className="w-full" />
                    {order.initialPercentLeft != null && (
                      <span className={iniClass} title="Nivel al momento de cargar el pedido">
                        Ini: {order.initialPercentLeft}%
                      </span>
                    )}
                  </div>
                </td>
                <td className={`${tdClass} text-right tabular-nums`}>
                  <div className="flex flex-col items-end">
                    <span>{order.currentDaysLeft ?? EMPTY_VALUE}</span>
                    {order.initialDaysLeft != null && (
                      <span className={iniClass}>Ini: {order.initialDaysLeft}</span>
                    )}
                  </div>
                </td>
                <td className={`${tdClass} text-right tabular-nums`}>
                  <div className="flex flex-col items-end">
                    <span>{order.currentPagesLeft ?? EMPTY_VALUE}</span>
                    {order.initialPagesLeft != null && (
                      <span className={iniClass}>Ini: {order.initialPagesLeft}</span>
                    )}
                  </div>
                </td>
                <td className={tdClass}>
                  <div className="flex flex-col items-start gap-1">
                    <StatusBadge tone="neutral">{order.supplyStatus}</StatusBadge>
                    {order.statusKey && (
                      <StatusBadge tone={toneForStatusKey(order.statusKey)}>
                        {order.statusLabel ?? order.statusKey}
                      </StatusBadge>
                    )}
                  </div>
                </td>
                <td className={`${tdClass} font-mono`}>
                  {order.supplyUrl ? (
                    <a
                      href={order.supplyUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand-orange hover:underline"
                    >
                      {order.orderId}
                    </a>
                  ) : (
                    order.orderId
                  )}
                </td>
                <td className={`${tdClass} whitespace-nowrap text-muted-foreground`}>
                  {formatArgDateTime(order.createdAt)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
