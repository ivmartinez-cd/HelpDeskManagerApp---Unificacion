"use client";

import { Package } from "lucide-react";
import type { CustomerSummary, DashboardResponse } from "@/features/insumos/types/dashboard";
import { cn } from "@/shared/utils/cn";
import { fmtInt } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";
import { CardEmpty, CardLink, CountBadge } from "./dashboard-card-bits";

interface Severidad {
  key: "critical" | "urgent" | "warning" | "good";
  label: string;
  /** Clase de texto del valor (tokens semánticos, dark-aware). */
  tone: string;
  dot: string;
}

const SEVERIDADES: Severidad[] = [
  { key: "critical", label: "Críticos", tone: "text-destructive", dot: "bg-destructive" },
  { key: "urgent", label: "Urgentes", tone: "text-brand-orange", dot: "bg-brand-orange" },
  { key: "warning", label: "Atención", tone: "text-warning-foreground dark:text-warning", dot: "bg-warning" },
  { key: "good", label: "OK", tone: "text-success", dot: "bg-success" },
];

const TOP_CLIENTES = 8;

function clientesConPendientes(d: DashboardResponse): CustomerSummary[] {
  return d.perCustomer
    .filter((c) => c.pending > 0)
    .sort((a, b) => b.critical - a.critical || b.urgent - a.urgent || b.pending - a.pending)
    .slice(0, TOP_CLIENTES);
}

export function InsumosSinCargarCard({
  dashboard,
  loading,
  error,
  onRetry,
}: {
  dashboard: DashboardResponse | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}) {
  const pending = dashboard?.totals.pending ?? 0;
  const critical = dashboard?.totals.critical ?? 0;

  return (
    <DashboardCard
      icon={Package}
      title="Insumos sin cargar"
      subtitle="Solicitudes HP SDS pendientes"
      headerRight={
        dashboard && pending > 0 ? (
          <CountBadge value={pending} tone={critical > 0 ? "bad" : "warn"} />
        ) : undefined
      }
      loading={loading}
      error={error}
      onRetry={onRetry}
      footer={<CardLink href="/insumos">Ver solicitudes →</CardLink>}
    >
      {!dashboard ? (
        <CardEmpty>Sin datos disponibles.</CardEmpty>
      ) : pending === 0 ? (
        <CardEmpty>Sin solicitudes pendientes.</CardEmpty>
      ) : (
        <>
          <div className="grid grid-cols-4 gap-1.5">
            {SEVERIDADES.map((s) => {
              const valor = dashboard.totals[s.key] ?? 0;
              return (
                <div key={s.key} className="rounded-[8px] bg-surface-2 px-2 py-1.5 text-center">
                  <div
                    className={cn(
                      "font-heading text-[16px] font-extrabold leading-none tabular-nums",
                      valor > 0 ? s.tone : "text-muted-foreground",
                    )}
                  >
                    {fmtInt(valor)}
                  </div>
                  <div className="mt-1 flex items-center justify-center gap-1 font-body text-[10.5px] text-muted-foreground">
                    <span className={cn("h-1.5 w-1.5 rounded-full", s.dot)} aria-hidden="true" />
                    {s.label}
                  </div>
                </div>
              );
            })}
          </div>
          <ul className="mt-2 flex flex-col gap-0.5">
            {clientesConPendientes(dashboard).map((c) => (
              <li key={c.customerId} className="flex items-center justify-between gap-2 px-1 py-0.5">
                <span className="min-w-0 flex-1 truncate font-body text-[12.5px] font-semibold text-foreground/80">
                  {c.name}
                </span>
                <span className="shrink-0 font-body text-[11px] text-muted-foreground tabular-nums">
                  {c.critical > 0 && <span className="font-bold text-destructive">{c.critical} crít. · </span>}
                  {fmtInt(c.pending)} pend.
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </DashboardCard>
  );
}
