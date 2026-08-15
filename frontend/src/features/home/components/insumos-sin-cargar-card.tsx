"use client";

import { Package } from "lucide-react";
import Link from "next/link";
import type { DashboardResponse } from "@/features/insumos/types/dashboard";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import { DashboardCard } from "./dashboard-card";

const ORANGE = "#F7941D";
const RED = "#ef4444";
const YELLOW = "#eab308";
const GREEN = "#22c55e";

interface SeverityRow {
  label: string;
  value: number;
  color: string;
}

function severityRows(d: DashboardResponse): SeverityRow[] {
  const { totals, thresholds } = d;
  return [
    { label: `Críticos ≤${thresholds.critical}d`, value: totals.critical ?? 0, color: RED },
    { label: `Urgentes ≤${thresholds.urgent}d`, value: totals.urgent ?? 0, color: ORANGE },
    { label: `Atención ≤${thresholds.warning}d`, value: totals.warning ?? 0, color: YELLOW },
    { label: "OK", value: totals.good ?? 0, color: GREEN },
  ];
}

export function InsumosSinCargarCard({
  dashboard,
  loading,
  error,
}: {
  dashboard: DashboardResponse | null;
  loading: boolean;
  error: string | null;
}) {
  const pending = dashboard?.totals.pending ?? 0;

  return (
    <DashboardCard
      icon={Package}
      title="Insumos sin cargar"
      subtitle="Solicitudes HP SDS pendientes"
      headerRight={
        dashboard && pending > 0 ? (
          <span className="rounded-full bg-brand-orange/15 px-2 py-0.5 font-heading text-[12px] font-bold text-brand-orange">
            {pending}
          </span>
        ) : undefined
      }
      loading={loading}
      error={error}
    >
      {!dashboard ? (
        <p className="pt-3 font-body text-[13px] text-muted-foreground">Sin datos disponibles.</p>
      ) : pending === 0 ? (
        <p className="pt-3 font-body text-[13px] text-muted-foreground">
          Sin solicitudes pendientes.
        </p>
      ) : (
        <>
          <div className="mt-3 flex flex-col items-center">
            <p
              className={cn(
                "font-heading text-[42px] font-extrabold leading-none tabular-nums",
              )}
              style={{ color: ORANGE }}
            >
              {pending}
            </p>
            <p className="mt-1 font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
              sin cargar
            </p>
          </div>

          <ul className="mt-3 flex flex-col gap-1">
            {severityRows(dashboard).map((row) => (
              <li
                key={row.label}
                className="flex items-center justify-between rounded-[6px] px-2 py-1.5"
              >
                <span className="flex items-center gap-1.5 font-body text-[12px] text-foreground/75">
                  <span
                    className="inline-block h-2 w-2 shrink-0 rounded-full"
                    style={{ backgroundColor: row.color }}
                  />
                  {row.label}
                </span>
                <span
                  className="font-heading text-[13px] font-extrabold tabular-nums"
                  style={{ color: row.value > 0 ? row.color : undefined }}
                >
                  {row.value}
                </span>
              </li>
            ))}
          </ul>

          <Link href="/insumos" className={cn(brandButtonClasses(), "mt-3 w-full")}>
            Ver solicitudes →
          </Link>
        </>
      )}
    </DashboardCard>
  );
}
