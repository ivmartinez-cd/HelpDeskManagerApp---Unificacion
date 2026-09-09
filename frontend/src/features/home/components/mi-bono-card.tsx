"use client";

import { Award } from "lucide-react";
import type { MiResumenBono } from "@/features/bono-tecnicos/types/bono-tecnicos";
import { CardEmpty, CardLink, MiniStat } from "./dashboard-card-bits";
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

function fmtPuntaje(puntaje: number | null | undefined): string {
  return puntaje !== null && puntaje !== undefined ? puntaje.toFixed(2) : "—";
}

/** Ancho de barra relativo al mayor de los dos puntajes mostrados (sin un
 * tope teórico fijo, ver `calcular_puntaje`): igual criterio de autoescala
 * que ya usa el sparkline de evolución anual de gerencia. Piso de 4% para que
 * un puntaje bajo (pero no nulo) siga siendo visible. */
function widthPct(puntaje: number | null | undefined, max: number): number {
  if (!puntaje || max <= 0) return 0;
  return Math.max(4, Math.min(100, (puntaje / max) * 100));
}

export function MiBonoCard({
  resumen,
  anterior,
  loading,
  error,
  onRetry,
}: {
  resumen: MiResumenBono | null;
  anterior?: MiResumenBono | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}) {
  const max = Math.max(resumen?.puntaje ?? 0, anterior?.puntaje ?? 0);
  const variacion =
    resumen?.puntaje !== null && resumen?.puntaje !== undefined && anterior?.puntaje !== null && anterior?.puntaje !== undefined
      ? resumen.puntaje - anterior.puntaje
      : null;

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
        <div className="flex flex-col gap-2.5">
          <div className="flex items-baseline gap-2">
            <span className="font-heading text-[28px] font-extrabold leading-none tabular-nums text-foreground">
              {fmtPuntaje(resumen.puntaje)}
            </span>
            <span className="font-body text-[12px] text-muted-foreground">
              {resumen.dias} día{resumen.dias === 1 ? "" : "s"} cargados
            </span>
          </div>
          <div
            className="flex flex-col gap-1"
            role="img"
            aria-label={`Bono actual ${fmtPuntaje(resumen.puntaje)}, mes anterior ${fmtPuntaje(anterior?.puntaje)}`}
          >
            <span className="h-2 w-full overflow-hidden rounded-full bg-surface-2">
              <span
                className="block h-full rounded-full bg-brand-orange"
                style={{ width: `${widthPct(resumen.puntaje, max)}%` }}
              />
            </span>
            <span className="h-2 w-full overflow-hidden rounded-full bg-surface-2">
              <span
                className="block h-full rounded-full bg-brand-gray"
                style={{ width: `${widthPct(anterior?.puntaje, max)}%` }}
              />
            </span>
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            <MiniStat
              label={anterior ? labelPeriodo(anterior.periodo) : "Mes anterior"}
              value={fmtPuntaje(anterior?.puntaje)}
              className="text-foreground/70"
            />
            <MiniStat
              label="Variación"
              value={variacion === null ? "—" : `${variacion >= 0 ? "▲" : "▼"} ${Math.abs(variacion).toFixed(2)}`}
              className={variacion === null ? undefined : variacion >= 0 ? "text-success" : "text-destructive"}
            />
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
