"use client";

import { ExternalLink } from "lucide-react";
import { StatusBadge, TonerBar, toneForStatusKey } from "../shared";
import type { PendingOrderRow } from "../../types";
import { EMPTY_VALUE, formatArgDateTime } from "../../utils/format";
import { sdsDeviceUrl } from "./audit-events";

/** Sub-tabla de la fila expandida de "Pedidos Pendientes": un renglón por
 * pedido del cliente. Cada métrica muestra el valor de hoy y, abajo, el valor
 * "Ini:" del momento en que se cargó el pedido — la diferencia entre los dos
 * es lo que delata un consumible ya cambiado con el pedido todavía abierto. */

const thClass =
  "whitespace-nowrap px-2 py-2 text-left font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground";
const tdClass = "px-2 py-2 font-body text-[12px] text-foreground";
const iniClass = "font-body text-[10.5px] text-muted-foreground";

export function PendingOrdersDetail({ orders }: { orders: PendingOrderRow[] }) {
  return (
    <div className="overflow-x-auto rounded-[8px] border border-border bg-card">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-border">
            <th className={thClass}>Sucursal</th>
            <th className={thClass}>Serie</th>
            <th className={thClass}>Insumo</th>
            <th className={thClass}>SKU</th>
            <th className={`${thClass} text-right`}>Nivel</th>
            <th className={`${thClass} text-right`}>Días rest.</th>
            <th className={`${thClass} text-right`}>Págs. rest.</th>
            <th className={thClass}>Estado</th>
            <th className={thClass}>Pedido CD</th>
            <th className={thClass}>Cargado el</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => {
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
