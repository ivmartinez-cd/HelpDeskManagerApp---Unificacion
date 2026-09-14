"use client";

import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";
import { Award } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Line } from "react-chartjs-2";
import { useTheme } from "@/shared/components/theme-provider";
import type { MiBonoHistoria } from "../hooks/use-inicio-data";
import { chartTheme } from "../utils/chart-theme";
import { periodoLabel } from "../utils/inicio-format";
import { CardEmpty, CardLink, MiniStat } from "./dashboard-card-bits";
import { DashboardCard } from "./dashboard-card";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip);

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

function Tendencia({ historia }: { historia: MiBonoHistoria }) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setMounted(true), []);
  const tema = useMemo(() => chartTheme(), [resolvedTheme, mounted]); // eslint-disable-line react-hooks/exhaustive-deps

  const puntos = historia.resumenes
    .map((r, i) =>
      r && r.puntaje !== null ? { label: periodoLabel(historia.periodos[i]), puntaje: r.puntaje } : null,
    )
    .filter((p): p is { label: string; puntaje: number } => p !== null);
  if (puntos.length < 2) return null;
  const min = Math.floor(Math.min(...puntos.map((p) => p.puntaje))) - 1;
  const max = Math.ceil(Math.max(...puntos.map((p) => p.puntaje)));

  return (
    <div className="flex min-h-0 flex-1 flex-col short:hidden">
      <div className="mb-1 font-heading text-[10.5px] font-bold uppercase tracking-[.05em] text-muted-foreground">
        Tendencia · últimos {puntos.length} meses
      </div>
      {/* Tope de alto, igual criterio que "SLA del mes": en monitores 2K la
          card queda muy alta y la sparkline estirada se ve desproporcionada. */}
      <div className="relative max-h-[140px] min-h-[40px] flex-1">
        <Line
          key={resolvedTheme}
          data={{
            labels: puntos.map((p) => p.label),
            datasets: [
              {
                data: puntos.map((p) => p.puntaje),
                borderColor: tema.orange,
                backgroundColor: (ctx) => {
                  const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, 56);
                  g.addColorStop(0, "rgba(247,148,29,.35)");
                  g.addColorStop(1, "rgba(247,148,29,0)");
                  return g;
                },
                fill: true,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                pointBackgroundColor: tema.orange,
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: { callbacks: { label: (c) => ` ${(c.raw as number).toFixed(2)}` } },
            },
            scales: {
              x: { grid: { display: false }, ticks: { color: tema.tick, font: { size: 10 } } },
              y: { display: false, min, max },
            },
          }}
        />
      </div>
    </div>
  );
}

/** "Mi bono" con el mismo tratamiento que "SLA del mes"
 * (`sla-mes-card.tsx`): número grande del mes actual, comparación con el mes
 * anterior + variación, y tendencia real de 6 meses (Chart.js). */
export function MiBonoCard({
  historia,
  loading,
  error,
  onRetry,
}: {
  historia: MiBonoHistoria | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}) {
  const resumenes = historia?.resumenes ?? [];
  const actual = resumenes[resumenes.length - 1] ?? null;
  const anterior = resumenes.length > 1 ? (resumenes[resumenes.length - 2] ?? null) : null;
  const variacion =
    actual?.puntaje !== null &&
    actual?.puntaje !== undefined &&
    anterior?.puntaje !== null &&
    anterior?.puntaje !== undefined
      ? actual.puntaje - anterior.puntaje
      : null;

  return (
    <DashboardCard
      icon={Award}
      title="Mi bono"
      subtitle={actual ? labelPeriodo(actual.periodo) : "Puntaje del mes en curso"}
      loading={loading}
      error={error}
      onRetry={onRetry}
      footer={<CardLink href="/tareas-varias">Ver mis Tareas Varias →</CardLink>}
    >
      {!actual ? (
        <CardEmpty>Sin datos disponibles.</CardEmpty>
      ) : (
        <div className="flex min-h-0 flex-1 flex-col gap-2.5">
          <div className="flex items-baseline gap-2">
            <span className="font-heading text-[28px] font-extrabold leading-none tabular-nums text-foreground">
              {fmtPuntaje(actual.puntaje)}
            </span>
            <span className="font-body text-[12px] text-muted-foreground">
              {actual.dias} día{actual.dias === 1 ? "" : "s"} cargados
            </span>
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            <MiniStat label="Mes ant." value={fmtPuntaje(anterior?.puntaje)} className="text-foreground/70" />
            <MiniStat
              label="Variación"
              value={variacion === null ? "—" : `${variacion >= 0 ? "▲" : "▼"} ${Math.abs(variacion).toFixed(2)}`}
              className={variacion === null ? undefined : variacion >= 0 ? "text-success" : "text-destructive"}
            />
          </div>
          <div className="flex gap-2 font-body text-[12.5px] text-muted-foreground">
            <span>
              TV: <strong className="text-foreground">{actual.tv_aprobadas}</strong> aprobadas
            </span>
            <span>·</span>
            <span>
              <strong className="text-foreground">{actual.tv_pendientes}</strong> pendientes
            </span>
          </div>
          {historia && <Tendencia historia={historia} />}
        </div>
      )}
    </DashboardCard>
  );
}
