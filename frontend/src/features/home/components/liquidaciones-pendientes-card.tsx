"use client";

import { FileText } from "lucide-react";
import Link from "next/link";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import { fmtInt } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";
import { OperadorDonut } from "./operador-donut";

type PorEstado = { abierta: number; preliquidada: number; recibida: number; observada: number };

const ESTADO_COLOR: Record<keyof PorEstado, string> = {
  abierta: "#6b9bb8",
  preliquidada: "#e07c39",
  recibida: "#7a7a7a",
  observada: "#c4a35a",
};

const ESTADO_LABEL: Record<keyof PorEstado, string> = {
  abierta: "Abierta",
  preliquidada: "Preliquidada",
  recibida: "Recibida",
  observada: "Observada",
};

const ESTADOS_ORDEN: (keyof PorEstado)[] = ["abierta", "preliquidada", "recibida", "observada"];

export function LiquidacionesPendientesCard({
  data,
  loading,
  error,
}: {
  data: { pendientes: number; porEstado: PorEstado } | null;
  loading: boolean;
  error: string | null;
}) {
  const total = data?.pendientes ?? 0;

  const rows = data
    ? ESTADOS_ORDEN.filter((k) => data.porEstado[k] > 0).map((k) => ({
        id: k,
        nombre: ESTADO_LABEL[k],
        color: ESTADO_COLOR[k],
        valor: data.porEstado[k],
      }))
    : [];

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
