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
import { Gauge, RotateCw } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Line } from "react-chartjs-2";
import { toast } from "sonner";
import { slaApi } from "@/features/sla/api/sla-api";
import type { SlaResumen } from "@/features/sla/types/sla";
import { useSession } from "@/services/session-provider";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import type { SlaHistoria } from "../hooks/use-inicio-data";
import { fmtInt, fmtPct, periodoLabel } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";
import { OperadorDonut } from "./operador-donut";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip);

const ORANGE = "#F7941D";
const RED = "#ef4444";

function slaRows(resumen: SlaResumen) {
  return [
    { id: "correctos", nombre: "Correctos", color: ORANGE, valor: resumen.correctos },
    { id: "vencidos", nombre: "Vencidos", color: RED, valor: resumen.vencidos },
  ];
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
  onSynced,
}: {
  historia: SlaHistoria | null;
  loading: boolean;
  error: string | null;
  onSynced?: () => void;
}) {
  const { user, can } = useSession();
  const canUpdate = user.isSuperadmin || can("sla", "update");
  const [syncing, setSyncing] = useState(false);

  const actual = historia?.resumenes[historia.resumenes.length - 1] ?? null;
  const anterior = historia?.resumenes[historia.resumenes.length - 2] ?? null;
  const variacion =
    actual && anterior && anterior.total > 0 ? actual.pct_correctos - anterior.pct_correctos : null;

  const handleSincronizar = async () => {
    const periodo = historia?.periodos[historia.periodos.length - 1];
    if (!periodo) return;
    setSyncing(true);
    try {
      await slaApi.refreshResumen(periodo);
      toast.success("SLA actualizado contra MERCURIO");
      onSynced?.();
    } catch {
      toast.error("Error al actualizar el SLA");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <DashboardCard
      icon={Gauge}
      title="SLA del mes"
      subtitle="Cumplimiento de acuerdos"
      loading={loading}
      error={error}
      headerRight={
        <button
          type="button"
          onClick={() => void handleSincronizar()}
          disabled={syncing || !historia || !canUpdate}
          title={canUpdate ? "Actualizar SLA (consulta completa a MERCURIO, ~40 s)" : "Sin permiso para actualizar"}
          aria-label="Actualizar SLA"
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-[6px] border border-border text-muted-foreground transition-colors hover:border-brand-orange/60 hover:text-brand-orange disabled:opacity-50"
        >
          <RotateCw className={cn("h-3.5 w-3.5", syncing && "animate-spin")} />
        </button>
      }
    >
      {!actual || actual.total === 0 ? (
        <span className="pt-3 font-body text-[13px] text-muted-foreground">
          Sin incidentes en el período actual.
        </span>
      ) : (
        <>
          <OperadorDonut
            rows={slaRows(actual)}
            total={actual.total}
            centerSub="incidentes"
            tooltipUnidad="incidentes"
          />
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
