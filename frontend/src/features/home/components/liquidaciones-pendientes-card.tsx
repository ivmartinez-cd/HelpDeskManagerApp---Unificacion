"use client";

import { FileText } from "lucide-react";
import Link from "next/link";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import { fmtInt } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";
import { OperadorDonut } from "./operador-donut";

const PALETTE = [
  "#e07c39", // brand orange
  "#6b9bb8", // blue
  "#c4a35a", // amber
  "#7a9b7a", // green
  "#9b7ab8", // purple
  "#b87a7a", // red
];

export function LiquidacionesPendientesCard({
  data,
  loading,
  error,
}: {
  data: { pendientes: number; porPrestador: { nombreCorto: string; count: number }[] } | null;
  loading: boolean;
  error: string | null;
}) {
  const total = data?.pendientes ?? 0;

  const rows = (data?.porPrestador ?? []).map((p, i) => ({
    id: p.nombreCorto,
    nombre: p.nombreCorto,
    color: PALETTE[i % PALETTE.length],
    valor: p.count,
  }));

  return (
    <DashboardCard
      icon={FileText}
      title="Liquidaciones sin aprobar"
      subtitle="Pendientes de aprobación"
      loading={loading}
      error={error}
      headerRight={
        data ? (
          <span className="shrink-0 font-heading text-[15px] font-extrabold text-amber-500">
            {fmtInt(total)}
          </span>
        ) : undefined
      }
    >
      {total === 0 ? (
        <span className="pt-3 font-body text-[13px] text-muted-foreground">
          No hay liquidaciones pendientes de aprobación.
        </span>
      ) : (
        <>
          <OperadorDonut
            rows={rows}
            total={total}
            centerSub="pendientes"
            tooltipUnidad="liquidaciones"
          />
          <Link href="/liquidaciones" className={cn(brandButtonClasses(), "mt-2.5 w-full")}>
            Ver liquidaciones →
          </Link>
        </>
      )}
    </DashboardCard>
  );
}
