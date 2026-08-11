"use client";

import { Fragment, useMemo, useState } from "react";
import { CheckCircle2, ChevronRight } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import type { DateRange, PendingOrderRow } from "../../types";
import { toArgDateKey } from "../../utils/format";
import { PendingOrdersDetail } from "./pending-orders-detail";

/** Pestaña "Pedidos Pendientes": los pedidos propios que siguen circulando en
 * Canal Directo, agrupados por cliente y expandibles (Patrón 1 del handoff,
 * mismo formato que el Dashboard). El detalle de cada grupo vive en
 * `pending-orders-detail.tsx`. */

interface PendingOrdersTableProps {
  orders: PendingOrderRow[];
  loading: boolean;
  search: string;
  range: DateRange | null;
  /** Deep-link `?customerId=` (desde el Dashboard o una notificación). */
  initialExpandedCustomerId: number | null;
}

interface CustomerGroup {
  customerId: number;
  customerName: string;
  orders: PendingOrderRow[];
}

function matchesSearch(order: PendingOrderRow, term: string): boolean {
  if (!term) return true;
  return [order.customerName, order.store, order.serial, order.description, order.sku].some(
    (field) => (field ?? "").toLowerCase().includes(term),
  );
}

/** El rango filtra por fecha de carga del pedido (`createdAt`), comparando
 * claves `YYYY-MM-DD` del día calendario argentino. */
function matchesRange(order: PendingOrderRow, range: DateRange | null): boolean {
  if (!range) return true;
  if (!order.createdAt) return false;
  const date = new Date(order.createdAt);
  if (Number.isNaN(date.getTime())) return false;
  const key = toArgDateKey(date);
  return key >= range.startDate && key <= range.endDate;
}

const headThClass =
  "px-4 py-2.5 font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground";

export function PendingOrdersTable({
  orders,
  loading,
  search,
  range,
  initialExpandedCustomerId,
}: PendingOrdersTableProps) {
  const [expanded, setExpanded] = useState<Set<number>>(
    () => new Set(initialExpandedCustomerId !== null ? [initialExpandedCustomerId] : []),
  );

  // El deep-link puede cambiar sin remontar el componente: se ajusta el estado
  // durante el render (mismo patrón que `date-range-picker.tsx`).
  const [prevDeepLink, setPrevDeepLink] = useState(initialExpandedCustomerId);
  if (initialExpandedCustomerId !== prevDeepLink) {
    setPrevDeepLink(initialExpandedCustomerId);
    if (initialExpandedCustomerId !== null) setExpanded(new Set([initialExpandedCustomerId]));
  }

  const groups = useMemo<CustomerGroup[]>(() => {
    const term = search.trim().toLowerCase();
    const map = new Map<number, CustomerGroup>();
    for (const order of orders) {
      if (!matchesSearch(order, term) || !matchesRange(order, range)) continue;
      const group = map.get(order.customerId);
      if (group) {
        group.orders.push(order);
      } else {
        map.set(order.customerId, {
          customerId: order.customerId,
          customerName: order.customerName || `Cliente ${order.customerId}`,
          orders: [order],
        });
      }
    }
    return [...map.values()].sort((a, b) => a.customerName.localeCompare(b.customerName, "es-AR"));
  }, [orders, search, range]);

  const toggle = (customerId: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(customerId)) next.delete(customerId);
      else next.add(customerId);
      return next;
    });
  };

  if (groups.length === 0) {
    return (
      <div className="mx-auto my-8 flex max-w-lg flex-col items-center gap-3 rounded-[12px] border border-border bg-card p-8 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[rgba(34,197,94,.1)] text-[#16a34a]">
          <CheckCircle2 className="h-6 w-6" aria-hidden="true" />
        </span>
        <h3 className="font-heading text-base font-bold text-foreground">
          {loading ? "Cargando pedidos…" : "¡Todo al día!"}
        </h3>
        <p className="font-body text-sm text-muted-foreground">
          {loading
            ? "Consultando Canal Directo e Insight."
            : search || range
              ? "Sin resultados para los filtros aplicados."
              : "No hay pedidos pendientes de entrega en este momento."}
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-border bg-muted/40">
            <th scope="col" className={`${headThClass} text-left`}>
              Cliente
            </th>
            <th scope="col" className={`${headThClass} text-right`}>
              Pendientes de entrega
            </th>
          </tr>
        </thead>
        <tbody>
          {groups.map((group) => {
            const isOpen = expanded.has(group.customerId);
            return (
              <Fragment key={group.customerId}>
                <tr
                  onClick={() => toggle(group.customerId)}
                  className="cursor-pointer select-none border-b border-border hover:bg-muted/30"
                >
                  <td className="px-4 py-2.5 font-body text-sm font-semibold text-foreground">
                    <span className="flex items-center gap-2">
                      <ChevronRight
                        className={cn(
                          "h-4 w-4 flex-none text-muted-foreground transition-transform",
                          isOpen && "rotate-90",
                        )}
                        aria-hidden="true"
                      />
                      {group.customerName}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right font-body text-sm tabular-nums text-foreground">
                    {group.orders.length}
                  </td>
                </tr>
                {isOpen && (
                  <tr className="border-b border-border bg-muted/20">
                    <td colSpan={2} className="px-4 py-4">
                      <PendingOrdersDetail orders={group.orders} />
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
