"use client";

import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  LineElement,
  LinearScale,
  PointElement,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { cn } from "@/shared/utils/cn";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler);

/** Tendencias KPI apagadas del handoff (NO neón). */
export const TREND_UP = "#8fb59a";
export const TREND_DOWN = "#c98484";
export const TREND_AMBER = "#c4a35a";

export interface KpiDef {
  label: string;
  /** null mientras carga; "—" si la fuente falló. */
  value: string | null;
  sub: string;
  valueColor?: string;
  trend?: { text: string; color: string } | null;
  /** Serie histórica real; sin historia no se dibuja sparkline (nada de
   * datos inventados — decisión explícita del proyecto). */
  spark?: { data: number[]; color: string } | null;
}

function Sparkline({ data, color }: { data: number[]; color: string }) {
  return (
    <div className="relative -mx-1 mt-0.5 h-[34px]">
      <Line
        data={{
          labels: data.map((_, i) => i),
          datasets: [
            {
              data,
              borderColor: color,
              backgroundColor: (ctx) => {
                const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, 34);
                g.addColorStop(0, `${color}26`);
                g.addColorStop(1, `${color}00`);
                return g;
              },
              fill: true,
              tension: 0.45,
              borderWidth: 1.5,
              pointRadius: 0,
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: { x: { display: false }, y: { display: false } },
        }}
      />
    </div>
  );
}

function KpiCard({ kpi }: { kpi: KpiDef }) {
  return (
    <div className="flex flex-col gap-1.5 rounded-[13px] border border-border bg-card px-4 pb-3 pt-[15px]">
      <div className="flex items-center justify-between gap-2">
        <span className="truncate font-heading text-[10.5px] font-bold uppercase tracking-[.05em] text-muted-foreground">
          {kpi.label}
        </span>
        {kpi.trend && (
          <span
            className="shrink-0 font-body text-[11.5px] font-bold"
            style={{ color: kpi.trend.color }}
          >
            {kpi.trend.text}
          </span>
        )}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span
          className={cn(
            "font-heading text-[25px] font-extrabold leading-none tracking-[-.01em] text-foreground",
            kpi.value === null && "animate-pulse text-muted-foreground",
          )}
          style={kpi.valueColor && kpi.value !== null ? { color: kpi.valueColor } : undefined}
        >
          {kpi.value ?? "…"}
        </span>
        <span className="truncate font-body text-[11.5px] text-muted-foreground">{kpi.sub}</span>
      </div>
      {kpi.spark && kpi.spark.data.length >= 2 && <Sparkline {...kpi.spark} />}
    </div>
  );
}

export function KpiStrip({ kpis }: { kpis: KpiDef[] }) {
  if (kpis.length === 0) return null;
  return (
    <div
      className="grid gap-3.5"
      style={{ gridTemplateColumns: `repeat(${kpis.length}, minmax(0, 1fr))` }}
    >
      {kpis.map((kpi) => (
        <KpiCard key={kpi.label} kpi={kpi} />
      ))}
    </div>
  );
}
