"use client";

import { Award } from "lucide-react";
import type { MiResumenBono } from "@/features/bono-tecnicos/types/bono-tecnicos";
import { CardEmpty, CardLink } from "./dashboard-card-bits";
import { DashboardCard } from "./dashboard-card";

const MESES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
];

function labelPeriodo(periodo: number): string {
  const mes = MESES[(periodo % 100) - 1] ?? String(periodo % 100);
  return `${mes} ${Math.floor(periodo / 100)}`;
}

export function MiBonoCard({
  resumen,
  loading,
  error,
  onRetry,
}: {
  resumen: MiResumenBono | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}) {
  return (
    <DashboardCard
      icon={Award}
      title="Mi bono"
      subtitle={resumen ? labelPeriodo(resumen.periodo) : "Puntaje del mes en curso"}
      loading={loading}
      error={error}
      onRetry={onRetry}
      footer={<CardLink href="/tareas-varias">Ver mis Tareas Varias →</CardLink>}
    >
      {!resumen ? (
        <CardEmpty>Sin datos disponibles.</CardEmpty>
      ) : (
        <div className="flex flex-col gap-3">
          <div>
            <div className="font-heading text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
              Puntaje
            </div>
            <div className="font-heading text-[28px] font-extrabold tabular-nums text-foreground">
              {resumen.puntaje !== null ? resumen.puntaje.toFixed(2) : "Sin calcular"}
            </div>
          </div>
          <div className="flex gap-2 font-body text-[12.5px] text-muted-foreground">
            <span>
              TV: <strong className="text-foreground">{resumen.tv_aprobadas}</strong> aprobadas
            </span>
            <span>·</span>
            <span>
              <strong className="text-foreground">{resumen.tv_pendientes}</strong> pendientes
            </span>
          </div>
        </div>
      )}
    </DashboardCard>
  );
}
