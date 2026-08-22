"use client";

import { Printer } from "lucide-react";
import type { PrestadoresResumen } from "@/features/prestadores/types/prestadores";
import { fmtInt, fmtPct } from "../utils/inicio-format";
import { agruparParque } from "../utils/parque";
import { DashboardCard } from "./dashboard-card";
import { BarRow, CardEmpty, CardLink } from "./dashboard-card-bits";

/** Parque de impresoras por operador (feature prestadores-card-parque):
 * barras ordenadas en vez de la dona anterior. Vive en "Seguimiento": es un
 * dato casi estático, no algo que se opera en el día. */
export function ParqueCard({
  resumen,
  loading,
  error,
  onRetry,
}: {
  resumen: PrestadoresResumen | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}) {
  const rows = resumen ? agruparParque(resumen) : [];
  const total = rows.reduce((sum, r) => sum + r.valor, 0);
  const max = Math.max(1, ...rows.map((r) => r.valor));

  return (
    <DashboardCard
      icon={Printer}
      title="Parque"
      subtitle="Impresoras por operador · PST activos"
      loading={loading}
      error={error}
      onRetry={onRetry}
      headerRight={
        rows.length > 0 ? (
          <span className="font-heading text-[14px] font-extrabold tabular-nums text-brand-orange">
            {fmtInt(total)}
            <span className="ml-1 font-body text-[11px] font-normal text-muted-foreground">impresoras</span>
          </span>
        ) : undefined
      }
      footer={<CardLink href="/prestadores">Ver prestadores →</CardLink>}
    >
      {rows.length === 0 ? (
        <CardEmpty>No hay prestadores activos cargados.</CardEmpty>
      ) : (
        <div className="flex flex-col gap-1.5">
          {rows.map((r) => (
            <BarRow
              key={r.id}
              color={r.color}
              label={r.nombre}
              detail={r.detalle}
              value={fmtInt(r.valor)}
              pct={total > 0 ? `${fmtPct(Math.round((r.valor / total) * 1000) / 10)}%` : undefined}
              widthPct={(r.valor / max) * 100}
            />
          ))}
        </div>
      )}
    </DashboardCard>
  );
}
