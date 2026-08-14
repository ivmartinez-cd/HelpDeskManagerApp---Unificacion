"use client";

import { ClipboardList } from "lucide-react";
import Link from "next/link";
import type { PendientesResumen } from "../types/pendientes";
import { DashboardCard } from "@/features/home/components/dashboard-card";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";

function textoFrescura(updatedAt: string): string {
  const diffMs = Date.now() - new Date(updatedAt).getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 2) return "hace un momento";
  if (mins < 60) return `hace ${mins} min`;
  const hs = Math.round(mins / 60);
  return `hace ${hs} h`;
}

export function PendientesACerrarCard({
  resumen,
  loading,
  error,
}: {
  resumen: PendientesResumen | null;
  loading: boolean;
  error: string | null;
}) {
  const total = resumen?.total ?? 0;

  return (
    <DashboardCard
      icon={ClipboardList}
      title="Pendientes a cerrar"
      subtitle="Incidentes Finalizados sin cerrar"
      headerRight={
        resumen && total > 0 ? (
          <span className="rounded-full bg-amber-500/15 px-2 py-0.5 font-heading text-[12px] font-bold text-amber-400">
            {total}
          </span>
        ) : undefined
      }
      loading={loading}
      error={error}
    >
      {!resumen || total === 0 ? (
        <p className="pt-3 font-body text-[13px] text-muted-foreground">
          {resumen ? "Sin incidentes pendientes a cerrar." : "Sin datos disponibles."}
        </p>
      ) : (
        <>
          <ul className="mt-2.5 flex max-h-[120px] flex-col gap-1 overflow-y-auto pr-1">
            {resumen.por_operador.map((op) => (
              <li
                key={op.operador_nombre}
                className="flex items-center justify-between gap-2 rounded-[6px] px-2 py-1.5 hover:bg-white/[.03]"
              >
                <span className="min-w-0 flex-1 truncate font-body text-[12px] text-foreground/80">
                  {op.operador_nombre}
                </span>
                <span className="shrink-0 rounded-full bg-amber-500/15 px-1.5 py-0.5 font-heading text-[11px] font-bold text-amber-400">
                  {op.cantidad}
                </span>
              </li>
            ))}
          </ul>

          <p className="mt-2 font-body text-[10px] text-muted-foreground/60">
            Actualizado {textoFrescura(resumen.updated_at)}
          </p>

          <Link href="/sla/pendientes-a-cerrar" className={brandButtonClasses() + " mt-3 w-full"}>
            Ver detalle →
          </Link>
        </>
      )}
    </DashboardCard>
  );
}
