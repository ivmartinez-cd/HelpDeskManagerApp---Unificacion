"use client";

import { CheckCircle2, CalendarCheck2 } from "lucide-react";
import Link from "next/link";
import type { CalendarEvent, ResumenClientesOperador } from "@/features/contadores/types/calendario";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import { DashboardCard } from "./dashboard-card";

function getCierreDate(): { labelCorto: string; diasRestantes: number } {
  const hoy = new Date();
  const mes = String(hoy.getMonth() + 1).padStart(2, "0");
  return { labelCorto: `20/${mes}`, diasRestantes: 20 - hoy.getDate() };
}

function toneFor(sinCerrar: number, diasRestantes: number) {
  if (sinCerrar === 0)   return { num: "text-emerald-400", badge: "bg-emerald-500/15 text-emerald-400" };
  if (diasRestantes > 5) return { num: "text-amber-400",   badge: "bg-amber-500/15 text-amber-400" };
  return                        { num: "text-red-400",      badge: "bg-red-500/15 text-red-400" };
}

export function CierreMensualCard({
  pendientes,
  resumen,
  loading,
  error,
}: {
  pendientes: CalendarEvent[];
  resumen: ResumenClientesOperador | null;
  loading: boolean;
  error: string | null;
}) {
  const sinCerrar = pendientes.length;
  const total = resumen?.total_clientes ?? null;
  const cerrados = total !== null ? Math.max(0, total - sinCerrar) : null;
  const pct = cerrados !== null && total && total > 0 ? (cerrados / total) * 100 : null;
  const { labelCorto, diasRestantes } = getCierreDate();
  const tone = toneFor(sinCerrar, diasRestantes);

  const subtituloFecha =
    sinCerrar === 0
      ? `Al día · cierre el ${labelCorto}`
      : diasRestantes > 0
      ? `${diasRestantes} ${diasRestantes === 1 ? "día" : "días"} para el cierre`
      : diasRestantes === 0
      ? "Cierre hoy"
      : `${Math.abs(diasRestantes)} ${Math.abs(diasRestantes) === 1 ? "día" : "días"} pasado el cierre`;

  return (
    <DashboardCard
      icon={CalendarCheck2}
      title="Cierre mensual"
      subtitle="Contadores del mes · Validación TL"
      loading={loading}
      error={error}
      headerRight={
        !loading && !error ? (
          <span className={`shrink-0 rounded-full px-2.5 py-0.5 font-heading text-[12px] font-extrabold ${tone.badge}`}>
            {labelCorto}
          </span>
        ) : undefined
      }
    >
      <div className="mt-3 flex flex-col gap-3">
        {sinCerrar === 0 ? (
          <div className="flex items-center gap-2 pt-1">
            <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-400" />
            <span className="font-heading text-[15px] font-extrabold text-emerald-400">
              Todos cerrados
            </span>
          </div>
        ) : (
          <div className="flex items-baseline gap-1.5 pt-1">
            <span className={`font-heading text-[36px] font-extrabold tabular-nums leading-none ${tone.num}`}>
              {sinCerrar}
            </span>
            <span className="font-body text-[13px] text-muted-foreground">
              {sinCerrar === 1 ? "cliente sin cerrar" : "clientes sin cerrar"}
              {total !== null && <> de {total}</>}
            </span>
          </div>
        )}

        {pct !== null && (
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-border/60">
            <div
              className="h-full rounded-full bg-brand-orange transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
        )}

        <span className="font-body text-[11px] text-muted-foreground">{subtituloFecha}</span>

        <Link href="/contadores/anexos-pendientes" className={cn(brandButtonClasses(), "mt-0.5 w-full")}>
          Ver anexos sin facturar →
        </Link>
      </div>
    </DashboardCard>
  );
}
