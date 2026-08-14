"use client";

import {
  ArcElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";
import { Gauge } from "lucide-react";
import Link from "next/link";
import { Doughnut, Line } from "react-chartjs-2";
import type { SlaResumen } from "@/features/sla/types/sla";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import type { SlaHistoria } from "../hooks/use-inicio-data";
import { fmtInt, fmtPct, periodoLabel } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";

ChartJS.register(ArcElement, CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip);

const ORANGE = "#F7941D";
const RED = "#ef4444";

function Dona({ resumen }: { resumen: SlaResumen }) {
  return (
    <div className="relative mx-auto my-2 flex h-[130px] w-[130px] items-center justify-center">
      <Doughnut
        data={{
          labels: ["Correctos", "Vencidos"],
          datasets: [
            {
              data: [resumen.correctos, resumen.vencidos],
              backgroundColor: [ORANGE, RED],
              borderWidth: 0,
              borderRadius: 6,
            },
          ],
        }}
        options={{
          cutout: "74%",
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          animation: { animateRotate: true, duration: 900 },
        }}
      />
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-heading text-[22px] font-extrabold leading-none text-brand-orange">
          {fmtPct(resumen.pct_correctos)}%
        </span>
        <span className="font-body text-[11px] text-muted-foreground">
          {fmtInt(resumen.correctos)} de {fmtInt(resumen.total)} correctos
        </span>
      </div>
    </div>
  );
}

function Tendencia({ historia }: { historia: SlaHistoria }) {
  const puntos = historia.resumenes
    .map((r, i) => (r && r.total > 0 ? { label: periodoLabel(historia.periodos[i]), pct: r.pct_correctos } : null))
    .filter((p): p is { label: string; pct: number } => p !== null);
  if (puntos.length < 2) return null;
  const min = Math.floor(Math.min(...puntos.map((p) => p.pct))) - 1;
  const max = Math.ceil(Math.max(...puntos.map((p) => p.pct)));

  return (
    <>
      <div className="mb-1.5 mt-2.5 font-heading text-[10px] font-bold uppercase tracking-[.05em] text-muted-foreground">
        Tendencia · últimos {puntos.length} meses
      </div>
      <div className="relative h-[44px]">
        <Line
          data={{
            labels: puntos.map((p) => p.label),
            datasets: [
              {
                data: puntos.map((p) => p.pct),
                borderColor: ORANGE,
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
                pointBackgroundColor: ORANGE,
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: { callbacks: { label: (c) => ` ${fmtPct(c.raw as number)}%` } },
            },
            scales: {
              x: { grid: { display: false }, ticks: { color: "rgba(255,255,255,.3)", font: { size: 9 } } },
              y: { display: false, min, max },
            },
          }}
        />
      </div>
    </>
  );
}

export function SlaMesCard({
  historia,
  loading,
  error,
}: {
  historia: SlaHistoria | null;
  loading: boolean;
  error: string | null;
}) {
  const actual = historia?.resumenes[historia.resumenes.length - 1] ?? null;
  const anterior = historia?.resumenes[historia.resumenes.length - 2] ?? null;
  const variacion =
    actual && anterior && anterior.total > 0 ? actual.pct_correctos - anterior.pct_correctos : null;

  return (
    <DashboardCard
      icon={Gauge}
      title="SLA del mes"
      subtitle="Cumplimiento de acuerdos"
      loading={loading}
      error={error}
    >
      {!actual || actual.total === 0 ? (
        <span className="pt-3 font-body text-[13px] text-muted-foreground">
          Sin incidentes en el período actual.
        </span>
      ) : (
        <>
          <Dona resumen={actual} />
          <div className="grid grid-cols-3 gap-2">
            <div className="rounded-[8px] bg-white/[.03] px-2.5 py-[9px] text-center">
              <div className="font-heading text-[9.5px] font-bold uppercase text-muted-foreground">
                Vencidos
              </div>
              <div className="mt-0.5 font-heading text-[15px] font-extrabold" style={{ color: RED }}>
                {fmtInt(actual.vencidos)}
              </div>
            </div>
            <div className="rounded-[8px] bg-white/[.03] px-2.5 py-[9px] text-center">
              <div className="font-heading text-[9.5px] font-bold uppercase text-muted-foreground">
                Mes ant.
              </div>
              <div className="mt-0.5 font-heading text-[15px] font-extrabold text-foreground/60">
                {anterior && anterior.total > 0 ? `${fmtPct(anterior.pct_correctos)}%` : "—"}
              </div>
            </div>
            <div className="rounded-[8px] bg-white/[.03] px-2.5 py-[9px] text-center">
              <div className="font-heading text-[9.5px] font-bold uppercase text-muted-foreground">
                Variación
              </div>
              <div
                className="mt-0.5 font-heading text-[15px] font-extrabold"
                style={{ color: variacion === null ? undefined : variacion >= 0 ? "#22c55e" : "#f87171" }}
              >
                {variacion === null
                  ? "—"
                  : `${variacion >= 0 ? "▲" : "▼"} ${fmtPct(Math.abs(variacion))}%`}
              </div>
            </div>
          </div>
          {historia && <Tendencia historia={historia} />}
          <Link href="/sla" className={cn(brandButtonClasses(), "mt-2.5 w-full")}>
            Ver detalle →
          </Link>
        </>
      )}
    </DashboardCard>
  );
}
