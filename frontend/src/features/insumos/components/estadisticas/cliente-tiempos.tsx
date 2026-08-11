import type { ReactNode } from "react";
import { EMPTY_VALUE, formatArgDateTime, formatNumber, formatPercent } from "../../utils/format";
import { formatDays, formatMinutes } from "./format-duration";
import type { FulfillmentStats, PendingToDispatchStats } from "../../types";

/** Los dos tiempos que el detalle de cliente mide sobre el mismo período:
 *  - **Atención**: de que HP SDS reporta la solicitud a que la app la carga en
 *    Canal Directo, contado solo dentro del horario laboral configurado.
 *  - **Pendiente → Despachado**: tránsito logístico dentro de Canal Directo, en
 *    días corridos.
 *
 * Los dos traen `measured`/`totalCreated`/`coveragePct`: no todos los pedidos
 * son medibles (los que siguen abiertos, los que no tienen fecha de destino),
 * y esconder esa cobertura haría ver el promedio como si fuera del total.
 */

interface TimeCardProps {
  title: string;
  subtitle: string;
  value: string;
  rows: { label: string; value: ReactNode }[];
  coverage: { measured: number; totalCreated: number; coveragePct: number };
}

function TimeCard({ title, subtitle, value, rows, coverage }: TimeCardProps) {
  return (
    <section data-print-card className="rounded-[12px] border border-border bg-card p-6">
      <h2 className="font-heading text-base font-bold text-foreground">{title}</h2>
      <p className="mt-0.5 font-body text-[13px] text-muted-foreground">{subtitle}</p>

      <div className="mt-4 font-heading text-[22px] font-extrabold leading-tight text-brand-orange">
        {value}
      </div>
      <p className="mt-1 font-body text-xs text-muted-foreground">
        Promedio sobre {formatNumber(coverage.measured)} de {formatNumber(coverage.totalCreated)}{" "}
        pedidos ({formatPercent(coverage.coveragePct, 0)} de cobertura)
      </p>

      <dl className="mt-4 flex flex-col gap-2 border-t border-border pt-4">
        {rows.map((row) => (
          <div key={row.label} className="flex flex-wrap items-baseline justify-between gap-2">
            <dt className="font-body text-[13px] text-muted-foreground">{row.label}</dt>
            <dd className="font-body text-[13px] font-semibold text-foreground">{row.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

/** "SKU · serie" del peor caso, tolerando que falte cualquiera de los dos. */
function worstTarget(sku?: string | null, deviceSerial?: string | null): string {
  const parts = [sku, deviceSerial].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : EMPTY_VALUE;
}

export function TiemposCliente({
  fulfillment,
  pendingToDispatch,
}: {
  fulfillment: FulfillmentStats;
  pendingToDispatch: PendingToDispatchStats;
}) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <TimeCard
        title="Tiempo de atención"
        subtitle={`De la solicitud de HP SDS a la carga en Canal Directo, contando solo horario laboral (${fulfillment.workHourStart}:00 a ${fulfillment.workHourEnd}:00).`}
        value={formatMinutes(fulfillment.avgMinutes)}
        coverage={fulfillment}
        rows={[
          { label: "Máximo del período", value: formatMinutes(fulfillment.maxMinutes) },
          {
            label: "Peor caso",
            value: fulfillment.worst
              ? `${worstTarget(fulfillment.worst.sku, fulfillment.worst.deviceSerial)} — ${formatMinutes(
                  fulfillment.worst.minutes,
                )}`
              : EMPTY_VALUE,
          },
          {
            label: "Fecha del peor caso",
            value: fulfillment.worst ? formatArgDateTime(fulfillment.worst.createdAt) : EMPTY_VALUE,
          },
        ]}
      />

      <TimeCard
        title="Pendiente → Despachado"
        subtitle="Tránsito del pedido dentro de Canal Directo, en días corridos."
        value={formatDays(pendingToDispatch.avgDays)}
        coverage={pendingToDispatch}
        rows={[
          { label: "Máximo del período", value: formatDays(pendingToDispatch.maxDays) },
          {
            label: "Peor caso",
            value: pendingToDispatch.worst
              ? `${worstTarget(
                  pendingToDispatch.worst.sku,
                  pendingToDispatch.worst.deviceSerial,
                )} — ${formatDays(pendingToDispatch.worst.days)}`
              : EMPTY_VALUE,
          },
          {
            label: "Pedido del peor caso",
            value: pendingToDispatch.worst ? pendingToDispatch.worst.orderId : EMPTY_VALUE,
          },
        ]}
      />
    </div>
  );
}
